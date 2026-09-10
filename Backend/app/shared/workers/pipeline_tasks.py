from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass
from typing import Any

import structlog
from sqlalchemy import select

from app.domains.meetings.infra.orm_models import MeetingORM
from app.domains.meetings.domain.entities import ProcessingStatus
from app.shared.events.event_types import DomainEvent, EventType, Stream
from app.shared.events.producer import get_producer
from app.shared.workers.async_runner import run_async
from app.shared.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


async def _run_pipeline_impl(meeting_id: str, org_id: str) -> dict[str, Any]:
    from app.domains.extraction.application.commands import RunPipelineCommand
    from app.domains.extraction.application.pipeline_service import PipelineService
    from app.domains.extraction.infra.decision_repo import SQLDecisionRepository
    from app.domains.extraction.infra.memory_repo import SQLMemoryRepository
    from app.domains.extraction.infra.repositories import SQLOpenQuestionRepository
    from app.domains.extraction.infra.risk_repo import SQLRiskRepository
    from app.domains.extraction.infra.task_repo import SQLActionItemRepository
    from app.domains.identity.infra.repositories import SQLUserRepository
    from app.domains.meetings.domain.entities import ProcessingStatus
    from app.domains.meetings.infra.repositories import SQLMeetingRepository, SQLTranscriptRepository
    from app.domains.meetings.infra.s3_adapter import B2Storage
    from app.shared.database import get_db_context, set_tenant_context
    from app.shared.events.event_types import Stream
    from app.shared.events.producer import get_producer

    mid = uuid.UUID(meeting_id)
    oid = uuid.UUID(org_id)

    producer = get_producer()
    await producer.connect()

    async def event_publisher(event: Any) -> None:
        if isinstance(event, DomainEvent):
            await producer.publish(Stream.EXTRACTION, event)
            return

        if is_dataclass(event):
            payload = asdict(event)
            payload.pop("event_id", None)
            payload.pop("org_id", None)
            payload.pop("occurred_at", None)

            event_type_map = {
                "PipelineStarted": EventType.PIPELINE_STARTED,
                "PipelineCompleted": EventType.PIPELINE_COMPLETED,
                "PipelineFailed": EventType.PIPELINE_FAILED,
                "TaskCreated": EventType.TASK_CREATED,
                "RiskFlagged": EventType.RISK_FLAGGED,
                "TaskAssigned": EventType.TASK_ASSIGNED,
                "TaskStatusChanged": EventType.TASK_STATUS_CHANGED,
                "DecisionExtracted": EventType.DECISION_EXTRACTED,
            }

            event_type = event_type_map.get(type(event).__name__, type(event).__name__.lower())

            domain_event = DomainEvent.create(
                event_type=event_type,
                org_id=event.org_id,
                payload=payload,
            )
            await producer.publish(Stream.EXTRACTION, domain_event)
            return

        await producer.publish(Stream.EXTRACTION, event)

    async with get_db_context() as db:
        await set_tenant_context(db, oid)

        meeting_repo = SQLMeetingRepository(db)

        async def meeting_updater(
            *,
            meeting_id: uuid.UUID,
            org_id: uuid.UUID,
            status: str,
            stage: int | None = None,
            stage_name: str | None = None,
            elapsed_ms: float | None = None,
            error: str | None = None,
        ) -> None:
            meeting = await meeting_repo.get_by_id(meeting_id, org_id)
            if not meeting:
                return
            if status and status != meeting.status:
                if ProcessingStatus.can_transition(meeting.status, status):
                    meeting.transition_status(status)
            if stage is not None and stage_name is not None:
                meeting.set_stage(stage, stage_name)
            if elapsed_ms is not None and stage_name:
                timings = dict(meeting.processing_meta.get("stage_timings") or {})
                timings[stage_name] = elapsed_ms
                meeting.processing_meta["stage_timings"] = timings
            if error:
                meeting.record_error(error, stage)
            await meeting_repo.update(meeting)

        meeting = await meeting_repo.get_by_id(mid, oid)
        if meeting and ProcessingStatus.can_transition(meeting.status, ProcessingStatus.QUEUED):
            meeting.transition_status(ProcessingStatus.QUEUED)
            await meeting_repo.update(meeting)

        try:
            s3 = B2Storage()
        except RuntimeError:
            s3 = None

        pipeline_service = PipelineService(
            decision_repo=SQLDecisionRepository(db),
            task_repo=SQLActionItemRepository(db),
            risk_repo=SQLRiskRepository(db),
            question_repo=SQLOpenQuestionRepository(db),
            memory_repo=SQLMemoryRepository(db),
            meeting_repo=meeting_repo,
            transcript_repo=SQLTranscriptRepository(db),
            s3_client=s3,
            user_repo=SQLUserRepository(db),
            db=db,
            meeting_updater=meeting_updater,
            event_publisher=event_publisher,
        )

        result = await pipeline_service.run(RunPipelineCommand(meeting_id=mid, org_id=oid))

        return {
            "meeting_id": meeting_id,
            "decisions": len(result.decisions),
            "tasks": len(result.action_items),
            "risks": len(result.risks),
            "questions": len(result.open_questions),
            "tokens": result.total_tokens_used,
        }


@celery_app.task(name="app.shared.workers.pipeline_tasks.run_pipeline", bind=True, max_retries=3)
def run_pipeline(self, meeting_id: str, org_id: str) -> dict[str, Any]:
    logger.info("pipeline_task_started", meeting_id=meeting_id, org_id=org_id)
    try:
        return run_async(_run_pipeline_impl(meeting_id, org_id))
    except Exception as exc:
        logger.error("pipeline_task_failed", meeting_id=meeting_id, org_id=org_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


async def _retry_incomplete_pipelines_impl() -> dict[str, Any]:
    from app.shared.database import get_db_context

    total = 0
    async with get_db_context() as db:
        query = select(MeetingORM.id, MeetingORM.org_id).where(
            MeetingORM.status.in_([ProcessingStatus.UPLOADED, ProcessingStatus.FAILED]),
            MeetingORM.deleted_at.is_(None),
        )
        result = await db.execute(query)
        rows = result.fetchall()
        for meeting_id, org_id in rows:
            try:
                run_pipeline.delay(str(meeting_id), str(org_id))
                total += 1
            except Exception:
                pass
    return {"requeued_meetings": total}


@celery_app.task(name="app.shared.workers.pipeline_tasks.retry_incomplete_pipelines", bind=True, max_retries=3)
def retry_incomplete_pipelines(self) -> dict[str, Any]:
    logger.info("retry_incomplete_pipelines_started")
    return run_async(_retry_incomplete_pipelines_impl())
