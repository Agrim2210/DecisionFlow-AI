   
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import structlog

from app.domains.extraction.domain.entities import (
    ActionItem,
    Decision,
    DecisionStatus,
    DecisionType,
    MemoryChunk,
    OpenQuestion,
    PipelineResult,
    QuestionStatus,
    Risk,
    RiskStatus,
    TaskPriority,
    TaskStatus,
)
from app.domains.extraction.domain.pipeline.clients.base_client import BaseAIClient
from app.domains.extraction.domain.pipeline.clients.groq_client import GroqClient
from app.domains.extraction.domain.pipeline.clients.gemini_embed_client import GeminiEmbedClient
from app.domains.extraction.domain.pipeline.clients.openai_embed_client import OpenAIEmbedClient
from app.shared.config import settings
from app.domains.extraction.domain.pipeline.stages.s1_normalizer import S1Normalizer
from app.domains.extraction.domain.pipeline.stages.s2_decision_extractor import (
    DecisionDraft,
    S2DecisionExtractor,
)
from app.domains.extraction.domain.pipeline.stages.s3_action_extractor import (
    ActionItemDraft,
    S3ActionExtractor,
)
from app.domains.extraction.domain.pipeline.stages.s4_dependency_detector import (
    DependencyDraft,
    S4DependencyDetector,
)
from app.domains.extraction.domain.pipeline.stages.s5_risk_analyzer import S5RiskAnalyzer
from app.domains.extraction.domain.pipeline.stages.s6_embedder import S6Embedder
from app.domains.extraction.domain.pipeline.stages.s7_question_extractor import S7QuestionExtractor

logger = structlog.get_logger(__name__)


class ExtractionPipeline:
       

    def __init__(
        self,
        ai_client: BaseAIClient | None = None,
        embed_client: BaseAIClient | None = None,
    ) -> None:
        _ai = ai_client or GroqClient()
        if embed_client is not None:
            _embed = embed_client
        elif settings.AI_EMBEDDING_MODEL.startswith("gemini"):
            _embed = GeminiEmbedClient()
        elif settings.AI_EMBEDDING_MODEL.startswith("text-embedding"):
            _embed = OpenAIEmbedClient()
        else:
            _embed = GeminiEmbedClient()

        self._s1 = S1Normalizer()
        self._s2 = S2DecisionExtractor(client=_ai)
        self._s3 = S3ActionExtractor(client=_ai)
        self._s4 = S4DependencyDetector(client=_ai)
        self._s5 = S5RiskAnalyzer(client=_ai)
        self._s6 = S6Embedder(client=_embed)
        self._s7 = S7QuestionExtractor(client=_ai)

    async def run(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        raw_transcript: str,
        known_users: list[dict] | None = None,
        meeting_date: datetime | None = None,
        on_stage_complete: "callable | None" = None,
    ) -> PipelineResult:
           
        total_tokens = 0
        timings: dict[str, float] = {}
        result = PipelineResult(meeting_id=meeting_id, org_id=org_id)

        async def _stage(num: int, name: str, coro):
            nonlocal total_tokens
            t = time.perf_counter()
            value = await coro
            elapsed = round((time.perf_counter() - t) * 1000, 1)
            timings[name] = elapsed
            logger.info("stage_complete", stage=num, name=name, elapsed_ms=elapsed)
            if on_stage_complete:
                try:
                    await on_stage_complete(num, name, elapsed)
                except Exception:
                    pass                                                   
            return value

                                                                    
        normalized = await _stage(
            1, "normalize",
            self._run_sync(self._s1.run, raw_transcript, known_users or []),
        )

                                                                    
        decision_drafts: list[DecisionDraft] = await _stage(
            2, "extract_decisions",
            self._s2.run(normalized.chunks),
        )

                                                                    
        task_drafts: list[ActionItemDraft] = await _stage(
            3, "extract_actions",
            self._s3.run(
                normalized.chunks,
                decision_drafts,
                normalized.speaker_map,
                meeting_date,
            ),
        )

                                                                    
        dep_drafts: list[DependencyDraft] = await _stage(
            4, "detect_dependencies",
            self._s4.run(task_drafts),
        )

                                                                    
        from app.domains.extraction.domain.pipeline.stages.s5_risk_analyzer import RiskDraft
        risk_drafts: list[RiskDraft] = await _stage(
            5, "analyze_risks",
            self._s5.run(decision_drafts, task_drafts, dep_drafts),
        )

                                                                   
        decision_ids = {d.title: uuid.uuid4() for d in decision_drafts}
        task_ids = {t.title: uuid.uuid4() for t in task_drafts}

                                                                    
        embed_result = await _stage(
            6, "embed",
            self._s6.run(
                org_id=org_id,
                meeting_id=meeting_id,
                decisions=decision_drafts,
                action_items=task_drafts,
                decision_ids=decision_ids,
                task_ids=task_ids,
                transcript_text=normalized.cleaned_text,
            ),
        )
        total_tokens += embed_result.total_tokens

                                                                    
        from app.domains.extraction.domain.pipeline.stages.s7_question_extractor import QuestionDraft
        question_drafts: list[QuestionDraft] = await _stage(
            7, "extract_questions",
            self._s7.run(normalized.chunks),
        )

                                                                    
        result.decisions = [
            self._draft_to_decision(d, decision_ids[d.title], meeting_id, org_id,
                                    embed_result.decision_embeddings.get(d.title))
            for d in decision_drafts
        ]

        result.action_items = [
            self._draft_to_task(t, task_ids[t.title], meeting_id, org_id,
                                decision_ids, embed_result.task_embeddings.get(t.title))
            for t in task_drafts
        ]

                                       
        title_to_decision_id = {d.title: decision_ids[d.title] for d in decision_drafts}
        title_to_task_id = {t.title: task_ids[t.title] for t in task_drafts}

        result.risks = [
            self._draft_to_risk(r, meeting_id, org_id, title_to_decision_id, title_to_task_id)
            for r in risk_drafts
        ]

        result.open_questions = [
            self._draft_to_question(q, meeting_id, org_id)
            for q in question_drafts
        ]

                                                                      
        result.dependency_edges = [
            {
                "upstream_title": d.upstream_title,
                "downstream_title": d.downstream_title,
                "dependency_type": d.dependency_type,
                "confidence_score": d.confidence_score,
                "detected_by": "ai",
            }
            for d in dep_drafts
        ]

        additional_memory = await self._s6.embed_additional_memory(
            org_id=org_id,
            meeting_id=meeting_id,
            documents=[
                (
                    "risk", risk.id, f"{risk.severity.title()} risk: {risk.risk_type}",
                    f"Risk: {risk.description} Recommendation: {risk.recommendation}",
                    {"severity": risk.severity, "risk_type": risk.risk_type, "status": risk.status},
                )
                for risk in result.risks
            ] + [
                (
                    "question", question.id, question.question,
                    f"Open question: {question.question} Context: {question.context}",
                    {"status": question.status},
                )
                for question in result.open_questions
            ],
        )
        result.memory_chunks = embed_result.memory_chunks + additional_memory
        result.stage_timings = timings
        result.total_tokens_used = total_tokens

        logger.info(
            "pipeline_complete",
            meeting_id=str(meeting_id),
            decisions=len(result.decisions),
            tasks=len(result.action_items),
            risks=len(result.risks),
            questions=len(result.open_questions),
            dependencies=len(result.dependency_edges),
            tokens=total_tokens,
        )
        return result

                                                                   

    @staticmethod
    def _draft_to_decision(
        d: DecisionDraft,
        decision_id: uuid.UUID,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        embedding: list[float] | None,
    ) -> Decision:
        return Decision(
            id=decision_id,
            org_id=org_id,
            meeting_id=meeting_id,
            title=d.title,
            description=d.description,
            decision_type=d.decision_type if d.decision_type in DecisionType.ALL else "operational",
            status=DecisionStatus.ACTIVE,
            confidence_score=d.confidence_score,
            ai_raw_output=d.raw_output,
            embedding=embedding,
        )

    @staticmethod
    def _draft_to_task(
        t: ActionItemDraft,
        task_id: uuid.UUID,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        decision_ids: dict[str, uuid.UUID],
        embedding: list[float] | None,
    ) -> ActionItem:
        decision_id = (
            decision_ids.get(t.related_decision_title)
            if t.related_decision_title
            else None
        )
        priority = t.priority if t.priority in TaskPriority.ALL else TaskPriority.MEDIUM
        return ActionItem(
            id=task_id,
            org_id=org_id,
            meeting_id=meeting_id,
            decision_id=decision_id,
            title=t.title,
            description=t.description,
            owner_id=t.owner_id,
            status=TaskStatus.PENDING,
            priority=priority,
            due_date=t.deadline_dt,
            confidence_score=t.confidence_score,
            ai_raw_output=t.raw_output,
            embedding=embedding,
        )

    @staticmethod
    def _draft_to_risk(
        r,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        decision_ids: dict[str, uuid.UUID],
        task_ids: dict[str, uuid.UUID],
    ) -> Risk:
        if r.related_item_type == "decision":
            related_id = decision_ids.get(r.related_item_title, uuid.uuid4())
        else:
            related_id = task_ids.get(r.related_item_title, uuid.uuid4())

        return Risk(
            id=uuid.uuid4(),
            org_id=org_id,
            meeting_id=meeting_id,
            related_item_id=related_id,
            related_item_type=r.related_item_type,
            risk_type=r.risk_type,
            severity=r.severity,
            description=r.description,
            recommendation=r.recommendation,
            status=RiskStatus.OPEN,
        )

    @staticmethod
    def _draft_to_question(q, meeting_id: uuid.UUID, org_id: uuid.UUID) -> OpenQuestion:
        return OpenQuestion(
            id=uuid.uuid4(),
            org_id=org_id,
            meeting_id=meeting_id,
            question=q.question,
            context=q.context,
            status=QuestionStatus.OPEN,
        )

    @staticmethod
    async def _run_sync(fn, *args):
                                                          
        return fn(*args)
