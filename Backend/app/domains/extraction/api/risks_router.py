   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.extraction.api.schemas import (
    QuestionListResponse,
    RiskListResponse,
    RiskResponse,
    UpdateRiskStatusRequest,
    AnswerQuestionRequest,
    OpenQuestionResponse,
    map_question,
    map_risk,
)
from app.domains.extraction.application.commands import (
    AnswerQuestionCommand,
    UpdateRiskStatusCommand,
)
from app.domains.extraction.application.extraction_service import ExtractionService
from app.domains.extraction.application.queries import (
    GetRiskQuery,
    ListQuestionsQuery,
    ListRisksQuery,
)
from app.domains.extraction.infra.repositories import (
    SQLActionItemRepository,
    SQLDecisionRepository,
    SQLMemoryRepository,
    SQLOpenQuestionRepository,
    SQLRiskRepository,
)
from app.shared.deps import AdminUser, CurrentUser, DBSession, MemberUser

router = APIRouter(tags=["Risks & Questions"])


def _svc(db) -> ExtractionService:
    return ExtractionService(
        decision_repo=SQLDecisionRepository(db),
        task_repo=SQLActionItemRepository(db),
        risk_repo=SQLRiskRepository(db),
        question_repo=SQLOpenQuestionRepository(db),
        memory_repo=SQLMemoryRepository(db),
    )


                                                                    

@router.get(
    "/risks",
    response_model=RiskListResponse,
    summary="[Admin] List all risks in the organization",
)
async def list_all_risks(
    current_user: AdminUser,
    db: DBSession,
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
) -> RiskListResponse:
    svc = _svc(db)
    risks = await svc.list_risks(
        ListRisksQuery(
            org_id=current_user.org_id,
            severity=severity,
            status=status,
            limit=limit,
        )
    )
    return RiskListResponse(risks=[map_risk(r) for r in risks])


@router.get(
    "/meetings/{meeting_id}/risks",
    response_model=RiskListResponse,
    summary="List risks detected in a meeting",
)
async def list_meeting_risks(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RiskListResponse:
    svc = _svc(db)
    risks = await svc.list_risks(
        ListRisksQuery(org_id=current_user.org_id, meeting_id=meeting_id)
    )
    return RiskListResponse(risks=[map_risk(r) for r in risks])


@router.get(
    "/risks/{risk_id}",
    response_model=RiskResponse,
    summary="Get a specific risk",
)
async def get_risk(
    risk_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> RiskResponse:
    svc = _svc(db)
    risk = await svc.get_risk(GetRiskQuery(risk_id=risk_id, org_id=current_user.org_id))
    return map_risk(risk)


@router.patch(
    "/risks/{risk_id}/status",
    response_model=RiskResponse,
    summary="Update risk status (acknowledge / resolve / dismiss)",
)
async def update_risk_status(
    risk_id: uuid.UUID,
    body: UpdateRiskStatusRequest,
    current_user: MemberUser,
    db: DBSession,
) -> RiskResponse:
    svc = _svc(db)
    risk = await svc.update_risk_status(
        UpdateRiskStatusCommand(
            risk_id=risk_id,
            org_id=current_user.org_id,
            updated_by=current_user.id,
            new_status=body.status,
        )
    )
    return map_risk(risk)


