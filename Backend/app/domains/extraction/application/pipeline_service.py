   
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog

from app.domains.extraction.application.commands import RunPipelineCommand
from app.domains.extraction.domain.entities import PipelineResult
from app.domains.extraction.domain.events import (
    PipelineCompleted,
    PipelineFailed,
    PipelineStarted,
    RiskFlagged,
    TaskCreated,
)
from app.domains.extraction.domain.repositories import (
    IActionItemRepository,
    IDecisionRepository,
    IMemoryRepository,
    IOpenQuestionRepository,
    IRiskRepository,
)
from app.domains.meetings.domain.entities import ProcessingStatus

logger = structlog.get_logger(__name__)


class PipelineService:
       

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        task_repo: IActionItemRepository,
        risk_repo: IRiskRepository,
        question_repo: IOpenQuestionRepository,
        memory_repo: IMemoryRepository,
        meeting_repo: Any = None,
        transcript_repo: Any = None,
        s3_client: Any = None,
        user_repo: Any = None,
        db: Any = None,
        meeting_updater: Any = None,
        event_publisher: Any = None,
    ) -> None:
        self._decisions = decision_repo
        self._tasks = task_repo
        self._risks = risk_repo
        self._questions = question_repo
        self._memory = memory_repo
        self._meetings = meeting_repo
        self._transcripts = transcript_repo
        self._s3 = s3_client
        self._users = user_repo
        self._db = db
        self._meeting_updater = meeting_updater
        self._event_publisher = event_publisher

    async def run(self, cmd: RunPipelineCommand) -> PipelineResult:
           
        existing = await self._decisions.list_by_meeting(cmd.meeting_id, cmd.org_id)
        if existing:
            logger.info(
                "pipeline_already_ran",
                meeting_id=str(cmd.meeting_id),
                existing_decisions=len(existing),
            )
            tasks = await self._tasks.list_by_meeting(cmd.meeting_id, cmd.org_id)
            risks = await self._risks.list_by_meeting(cmd.meeting_id, cmd.org_id)
            questions = await self._questions.list_by_meeting(cmd.meeting_id, cmd.org_id)
            result = PipelineResult(meeting_id=cmd.meeting_id, org_id=cmd.org_id)
            result.decisions = existing
            result.action_items = tasks
            result.risks = risks
            result.open_questions = questions
            return result

        raw_transcript, known_users, meeting_date = await self._load_pipeline_inputs(cmd)

        await self._update_meeting(
            cmd,
            status=ProcessingStatus.PROCESSING,
            stage=0,
            stage_name="starting",
        )
        await self._publish(PipelineStarted.create(cmd.org_id, cmd.meeting_id))

        async def on_stage_complete(stage_num: int, stage_name: str, elapsed_ms: float) -> None:
            await self._update_meeting(
                cmd,
                status=ProcessingStatus.PROCESSING,
                stage=stage_num,
                stage_name=stage_name,
                elapsed_ms=elapsed_ms,
            )

        try:
            from app.domains.extraction.domain.pipeline.pipeline import ExtractionPipeline

            pipeline = ExtractionPipeline()
            result = await pipeline.run(
                meeting_id=cmd.meeting_id,
                org_id=cmd.org_id,
                raw_transcript=raw_transcript,
                known_users=known_users,
                meeting_date=meeting_date,
                on_stage_complete=on_stage_complete,
            )
        except Exception as exc:
            logger.error("pipeline_failed", meeting_id=str(cmd.meeting_id), error=str(exc))
            await self._publish(PipelineFailed.create(
                cmd.org_id, cmd.meeting_id, stage=0, error=str(exc)
            ))
            await self._update_meeting(
                cmd,
                status=ProcessingStatus.FAILED,
                error=str(exc),
            )
            raise

        await self._persist(result)

        if result.dependency_edges:
            await self._persist_dependencies(result, cmd.org_id)

        await self._compute_analytics(cmd.meeting_id, cmd.org_id)

        await self._publish(PipelineCompleted.create(
            org_id=cmd.org_id,
            meeting_id=cmd.meeting_id,
            decisions_count=len(result.decisions),
            tasks_count=len(result.action_items),
            risks_count=len(result.risks),
            questions_count=len(result.open_questions),
            total_tokens_used=result.total_tokens_used,
        ))

        for task in result.action_items:
            await self._publish(TaskCreated.create(
                org_id=cmd.org_id, meeting_id=cmd.meeting_id,
                task_id=task.id, owner_id=task.owner_id,
                due_date=task.due_date, priority=task.priority,
            ))

        for risk in result.risks:
            if risk.severity in ("critical", "high"):
                await self._publish(RiskFlagged.create(
                    org_id=cmd.org_id, meeting_id=cmd.meeting_id,
                    risk_id=risk.id, risk_type=risk.risk_type,
                    severity=risk.severity, related_item_id=risk.related_item_id,
                    related_item_type=risk.related_item_type,
                ))

        await self._update_meeting(
            cmd,
            status=ProcessingStatus.COMPLETED,
            stage=7,
            stage_name="complete",
        )

        logger.info(
            "pipeline_complete",
            meeting_id=str(cmd.meeting_id),
            decisions=len(result.decisions),
            tasks=len(result.action_items),
            risks=len(result.risks),
            questions=len(result.open_questions),
            tokens=result.total_tokens_used,
        )
        return result

    async def _load_pipeline_inputs(
        self, cmd: RunPipelineCommand
    ) -> tuple[str, list[dict], datetime | None]:
        if not self._meetings or not self._transcripts:
            raise RuntimeError("Meeting and transcript repositories are required")

        meeting = await self._meetings.get_by_id(cmd.meeting_id, cmd.org_id)
        if not meeting:
            raise ValueError(f"Meeting {cmd.meeting_id} not found")

        transcript = await self._transcripts.get_by_meeting_id(cmd.meeting_id, cmd.org_id)
        if not transcript:
            raise ValueError(f"Transcript not found for meeting {cmd.meeting_id}")

        raw_text = transcript.raw_text
        if (not raw_text or not raw_text.strip()) and transcript.raw_s3_key:
            if not self._s3:
                raise ValueError(
                    "Transcript text is not stored in DB and S3 is not configured"
                )
            data = await self._s3.download_bytes(transcript.raw_s3_key)
            raw_text = data.decode("utf-8")

        if not raw_text or not raw_text.strip():
            raise ValueError("Transcript has no text content")

        known_users: list[dict] = []
        if self._users:
            users = await self._users.list_by_org(cmd.org_id, limit=500)
            known_users = [{"name": user.name, "id": str(user.id)} for user in users]

        return raw_text, known_users, meeting.meeting_date

    async def _update_meeting(
        self,
        cmd: RunPipelineCommand,
        *,
        status: str,
        stage: int | None = None,
        stage_name: str | None = None,
        elapsed_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        if not self._meeting_updater:
            return
        try:
            await self._meeting_updater(
                meeting_id=cmd.meeting_id,
                org_id=cmd.org_id,
                status=status,
                stage=stage,
                stage_name=stage_name,
                elapsed_ms=elapsed_ms,
                error=error,
            )
        except Exception as exc:
            logger.warning("meeting_update_failed", error=str(exc))

    async def _persist(self, result: PipelineResult) -> None:
                                                                                 
        if result.decisions:
            await self._decisions.bulk_create(result.decisions)
            logger.debug("decisions_persisted", count=len(result.decisions))

        if result.action_items:
            await self._tasks.bulk_create(result.action_items)
            logger.debug("tasks_persisted", count=len(result.action_items))

        if result.risks:
            await self._risks.bulk_create(result.risks)
            logger.debug("risks_persisted", count=len(result.risks))

        if result.open_questions:
            await self._questions.bulk_create(result.open_questions)
            logger.debug("questions_persisted", count=len(result.open_questions))

        if result.memory_chunks:
            await self._memory.bulk_create(result.memory_chunks)
            logger.debug("memory_chunks_persisted", count=len(result.memory_chunks))

    async def _persist_dependencies(self, result: PipelineResult, org_id: uuid.UUID) -> None:
                                                                          
        if not self._db:
            logger.warning("dependency_persistence_skipped", reason="no_db_session")
            return

        try:
            from app.domains.graph.application.commands import BulkAddDependenciesCommand
            from app.domains.graph.application.dependency_service import DependencyService
            from app.domains.graph.infra.dependency_repo import SQLDependencyRepository

            title_to_id: dict[str, uuid.UUID] = {t.title: t.id for t in result.action_items}

            resolved_edges = []
            for edge in result.dependency_edges:
                up_id = title_to_id.get(edge.get("upstream_title", ""))
                down_id = title_to_id.get(edge.get("downstream_title", ""))
                if up_id and down_id:
                    resolved_edges.append({
                        "upstream_id": up_id,
                        "downstream_id": down_id,
                        "dependency_type": edge.get("dependency_type", "finish_to_start"),
                        "confidence_score": edge.get("confidence_score", 0.9),
                    })

            if resolved_edges:
                dep_service = DependencyService(dep_repo=SQLDependencyRepository(self._db))
                created = await dep_service.bulk_add_from_pipeline(
                    BulkAddDependenciesCommand(org_id=org_id, edges=resolved_edges)
                )
                logger.info("dependencies_persisted", count=len(created))

        except Exception as exc:
            logger.warning("dependency_persistence_failed", error=str(exc))

    async def _compute_analytics(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> None:
        if not self._db:
            return

        try:
            from app.domains.analytics.application.analytics_service import AnalyticsService
            from app.domains.analytics.infra.analytics_repo import SQLMeetingAnalyticsRepository
            from app.domains.analytics.infra.snapshot_repo import SQLSnapshotRepository

            analytics_service = AnalyticsService(
                snapshot_repo=SQLSnapshotRepository(self._db),
                meeting_analytics_repo=SQLMeetingAnalyticsRepository(self._db),
                db=self._db,
            )
            await analytics_service.compute_meeting_analytics(meeting_id, org_id)
        except Exception as exc:
            logger.warning("meeting_analytics_failed", error=str(exc))

    async def _publish(self, event: Any) -> None:
                                                                       
        if self._event_publisher:
            try:
                await self._event_publisher(event)
            except Exception as exc:
                logger.warning("event_publish_failed", event_type=type(event).__name__, error=str(exc))
