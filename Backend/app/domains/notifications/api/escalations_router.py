   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.notifications.api.schemas import (
    EscalationListResponse,
    EscalationResponse,
    ResolveEscalationRequest,
    map_escalation,
)
from app.domains.notifications.application.commands import (
    DismissEscalationCommand,
    ResolveEscalationCommand,
)
from app.domains.notifications.application.escalation_service import EscalationService
from app.domains.notifications.application.queries import GetEscalationQuery, ListEscalationsQuery
from app.domains.notifications.infra.repositories import (
    SQLEscalationPolicyRepository,
    SQLEscalationRepository,
    SQLNotificationRepository,
)
from app.shared.deps import AdminUser, DBSession
from app.shared.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/escalations", tags=["Escalations"])


def _svc(db) -> EscalationService:
    return EscalationService(
        escalation_repo=SQLEscalationRepository(db),
        policy_repo=SQLEscalationPolicyRepository(db),
        notif_repo=SQLNotificationRepository(db),
        user_lookup=None,
    )


@router.get("", response_model=EscalationListResponse, summary="[Admin] List all escalations")
async def list_escalations(
    current_user: AdminUser, db: DBSession,
    status: str | None = Query(default=None, pattern=r"^(active|resolved|dismissed)$"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
) -> EscalationListResponse:
    svc = _svc(db)
    cursor_id = None
    if cursor:
        try:
            cursor_id = decode_cursor(cursor)
        except ValueError:
            pass

    escalations = await svc.list_escalations(ListEscalationsQuery(
        org_id=current_user.org_id, status=status, limit=limit, cursor_id=cursor_id,
    ))
    has_next = len(escalations) > limit
    page = escalations[:limit]
    return EscalationListResponse(
        escalations=[map_escalation(e) for e in page], has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


@router.get("/{escalation_id}", response_model=EscalationResponse, summary="[Admin] Get escalation detail")
async def get_escalation(escalation_id: uuid.UUID, current_user: AdminUser, db: DBSession) -> EscalationResponse:
    svc = _svc(db)
    escalation = await svc.get_escalation(GetEscalationQuery(
        escalation_id=escalation_id, org_id=current_user.org_id,
    ))
    return map_escalation(escalation)


@router.patch("/{escalation_id}", response_model=EscalationResponse, summary="[Admin] Resolve or dismiss")
async def update_escalation(
    escalation_id: uuid.UUID, body: ResolveEscalationRequest,
    current_user: AdminUser, db: DBSession,
) -> EscalationResponse:
    svc = _svc(db)
    if body.action == "resolve":
        escalation = await svc.resolve(ResolveEscalationCommand(
            escalation_id=escalation_id, org_id=current_user.org_id, resolved_by=current_user.id,
        ))
    else:
        escalation = await svc.dismiss(DismissEscalationCommand(
            escalation_id=escalation_id, org_id=current_user.org_id, dismissed_by=current_user.id,
        ))
    return map_escalation(escalation)
