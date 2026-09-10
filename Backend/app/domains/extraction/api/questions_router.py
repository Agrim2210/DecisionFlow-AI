   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.extraction.api.schemas import (
    AnswerQuestionRequest,
    OpenQuestionResponse,
    QuestionListResponse,
    map_question,
)
from app.domains.extraction.application.commands import AnswerQuestionCommand
from app.domains.extraction.application.extraction_service import ExtractionService
from app.domains.extraction.application.queries import ListQuestionsQuery
from app.domains.extraction.infra.repositories import (
    SQLActionItemRepository,
    SQLDecisionRepository,
    SQLMemoryRepository,
    SQLOpenQuestionRepository,
    SQLRiskRepository,
)
from app.shared.deps import CurrentUser, DBSession, MemberUser

router = APIRouter(tags=["Open Questions"])


def _svc(db) -> ExtractionService:
    return ExtractionService(
        decision_repo=SQLDecisionRepository(db),
        task_repo=SQLActionItemRepository(db),
        risk_repo=SQLRiskRepository(db),
        question_repo=SQLOpenQuestionRepository(db),
        memory_repo=SQLMemoryRepository(db),
    )


@router.get(
    "/meetings/{meeting_id}/questions",
    response_model=QuestionListResponse,
    summary="List open questions extracted from a meeting",
)
async def list_meeting_questions(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    status: str | None = Query(
        default=None,
        pattern=r"^(open|answered|deferred)$",
    ),
) -> QuestionListResponse:
    svc = _svc(db)
    questions = await svc.list_questions(
        ListQuestionsQuery(
            org_id=current_user.org_id,
            meeting_id=meeting_id,
            status=status,
        )
    )
    if status:
        questions = [q for q in questions if q.status == status]
    return QuestionListResponse(questions=[map_question(q) for q in questions])


@router.get(
    "/questions",
    response_model=QuestionListResponse,
    summary="List all open questions across the org",
)
async def list_all_questions(
    current_user: CurrentUser,
    db: DBSession,
    status: str | None = Query(default="open", pattern=r"^(open|answered|deferred)$"),
) -> QuestionListResponse:
    svc = _svc(db)
                                                                        
                                                            
    questions = await svc.list_questions(
        ListQuestionsQuery(org_id=current_user.org_id, status=status)
    )
    return QuestionListResponse(questions=[map_question(q) for q in questions])


@router.patch(
    "/questions/{question_id}/answer",
    response_model=OpenQuestionResponse,
    summary="Provide an answer to an open question",
)
async def answer_question(
    question_id: uuid.UUID,
    body: AnswerQuestionRequest,
    current_user: MemberUser,
    db: DBSession,
) -> OpenQuestionResponse:
    svc = _svc(db)
    question = await svc.answer_question(
        AnswerQuestionCommand(
            question_id=question_id,
            org_id=current_user.org_id,
            answered_by=current_user.id,
            answer=body.answer,
        )
    )
    return map_question(question)


@router.patch(
    "/questions/{question_id}/defer",
    response_model=OpenQuestionResponse,
    summary="Defer a question to a future discussion",
)
async def defer_question(
    question_id: uuid.UUID,
    current_user: MemberUser,
    db: DBSession,
) -> OpenQuestionResponse:
                                                                
    from app.domains.extraction.infra.repositories import SQLOpenQuestionRepository
    from app.domains.extraction.domain.exceptions import OpenQuestionNotFoundError

    repo = SQLOpenQuestionRepository(db)
    question = await repo.get_by_id(question_id, current_user.org_id)
    if not question:
        raise OpenQuestionNotFoundError()

    question.status = "deferred"
    from datetime import datetime, timezone
    question.updated_at = datetime.now(timezone.utc)
    updated = await repo.update(question)
    return map_question(updated)
