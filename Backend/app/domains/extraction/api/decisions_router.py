   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.extraction.api.schemas import (
    DecisionListResponse,
    DecisionResponse,
    MeetingExtractionResponse,
    UpdateDecisionRequest,
    map_decision,
    map_question,
    map_risk,
    map_task,
)
from app.domains.extraction.application.commands import UpdateDecisionCommand
from app.domains.extraction.application.extraction_service import ExtractionService
from app.domains.extraction.application.queries import (
    GetDecisionQuery,
    GetMeetingExtractionQuery,
    ListDecisionsQuery,
)
from app.domains.extraction.infra.decision_repo import SQLDecisionRepository
from app.domains.extraction.infra.task_repo import SQLActionItemRepository
from app.domains.extraction.infra.risk_repo import SQLRiskRepository
from app.domains.extraction.infra.memory_repo import SQLMemoryRepository
from app.domains.extraction.infra.repositories import SQLOpenQuestionRepository
from app.shared.deps import AdminUser, CurrentUser, DBSession, MemberUser
from app.shared.pagination import decode_cursor, encode_cursor

router = APIRouter(tags=["Decisions"])


                                                                     

def _svc(db) -> ExtractionService:
                                                                 
    return ExtractionService(
        decision_repo=SQLDecisionRepository(db),
        task_repo=SQLActionItemRepository(db),
        risk_repo=SQLRiskRepository(db),
        question_repo=SQLOpenQuestionRepository(db),
        memory_repo=SQLMemoryRepository(db),
    )


def _decode(cursor: str | None) -> uuid.UUID | None:
    if not cursor:
        return None
    try:
        return decode_cursor(cursor)
    except ValueError:
        return None


                                                                    

@router.get(
    "/meetings/{meeting_id}/extraction",
    response_model=MeetingExtractionResponse,
    summary="Get all AI-extracted entities for a meeting",
    description=(
        "Returns decisions, tasks, risks and open questions for this meeting. "
        "Available once meeting status is `completed`."
    ),
)
async def get_meeting_extraction(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MeetingExtractionResponse:
    svc = _svc(db)
    result = await svc.get_meeting_extraction(
        GetMeetingExtractionQuery(
            meeting_id=meeting_id,
            org_id=current_user.org_id,
        )
    )
    return MeetingExtractionResponse(
        meeting_id=meeting_id,
        decisions=[map_decision(d) for d in result.decisions],
        tasks=[map_task(t) for t in result.action_items],
        risks=[map_risk(r) for r in result.risks],
        open_questions=[map_question(q) for q in result.open_questions],
        summary={
            "decisions":      len(result.decisions),
            "tasks":          len(result.action_items),
            "risks":          len(result.risks),
            "open_questions": len(result.open_questions),
        },
    )


                                                                    

@router.get(
    "/meetings/{meeting_id}/decisions",
    response_model=list[DecisionResponse],
    summary="Get decisions extracted from a specific meeting",
)
async def list_meeting_decisions(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> list[DecisionResponse]:
    svc = _svc(db)
    decisions = await svc.list_decisions(
        ListDecisionsQuery(
            org_id=current_user.org_id,
            meeting_id=meeting_id,
        )
    )
    return [map_decision(d) for d in decisions]


                                                                   

@router.get(
    "/decisions",
    response_model=DecisionListResponse,
    summary="[Admin] List all decisions across the organization",
    description=(
        "Paginated list of all org decisions. "
        "Filter by `type` (strategic/operational/technical/financial) "
        "or `status` (active/superseded/cancelled). "
        "Pass `next_cursor` from previous response as `cursor` for next page."
    ),
)
async def list_all_decisions(
    current_user: AdminUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    type: str | None = Query(
        default=None,
        pattern=r"^(strategic|operational|technical|financial)$",
        description="Filter by decision type",
    ),
    status: str | None = Query(
        default=None,
        pattern=r"^(active|superseded|cancelled)$",
        description="Filter by status",
    ),
) -> DecisionListResponse:
    svc = _svc(db)
    decisions = await svc.list_decisions(
        ListDecisionsQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=_decode(cursor),
            decision_type=type,
            status=status,
        )
    )
    has_next = len(decisions) > limit
    page = decisions[:limit]
    return DecisionListResponse(
        decisions=[map_decision(d) for d in page],
        has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


                                                                    

@router.get(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    summary="Get a specific decision by ID",
)
async def get_decision(
    decision_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> DecisionResponse:
    svc = _svc(db)
    decision = await svc.get_decision(
        GetDecisionQuery(
            decision_id=decision_id,
            org_id=current_user.org_id,
        )
    )
    return map_decision(decision)


                                                                    

@router.patch(
    "/decisions/{decision_id}",
    response_model=DecisionResponse,
    summary="Update a decision (status, title, or description)",
    description=(
        "Partial update — only send fields you want to change. "
        "Status: active → superseded | cancelled (no reverse). "
        "All changes are audit-logged."
    ),
)
async def update_decision(
    decision_id: uuid.UUID,
    body: UpdateDecisionRequest,
    current_user: MemberUser,
    db: DBSession,
) -> DecisionResponse:
    svc = _svc(db)
    decision = await svc.update_decision(
        UpdateDecisionCommand(
            decision_id=decision_id,
            org_id=current_user.org_id,
            updated_by=current_user.id,
            status=body.status,
            title=body.title,
            description=body.description,
        )
    )
    return map_decision(decision)
