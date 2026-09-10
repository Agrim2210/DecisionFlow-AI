   
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.domains.notifications.api.schemas import (
    CreatePolicyRequest,
    EscalationPolicyResponse,
    PolicyListResponse,
    UpdatePolicyRequest,
    map_policy,
)
from app.domains.notifications.application.commands import CreatePolicyCommand, UpdatePolicyCommand
from app.domains.notifications.application.escalation_service import EscalationService
from app.domains.notifications.application.queries import ListPoliciesQuery
from app.domains.notifications.infra.repositories import (
    SQLEscalationPolicyRepository,
    SQLEscalationRepository,
    SQLNotificationRepository,
)
from app.shared.deps import AdminUser, DBSession

router = APIRouter(prefix="/escalation-policies", tags=["Escalation Policies"])


def _svc(db) -> EscalationService:
    return EscalationService(
        escalation_repo=SQLEscalationRepository(db),
        policy_repo=SQLEscalationPolicyRepository(db),
        notif_repo=SQLNotificationRepository(db),
    )


@router.get("", response_model=PolicyListResponse, summary="[Admin] List escalation policies")
async def list_policies(current_user: AdminUser, db: DBSession) -> PolicyListResponse:
    svc = _svc(db)
    policies = await svc.list_policies(ListPoliciesQuery(org_id=current_user.org_id))
    return PolicyListResponse(policies=[map_policy(p) for p in policies])


@router.post("", response_model=EscalationPolicyResponse, status_code=201, summary="[Admin] Create policy")
async def create_policy(body: CreatePolicyRequest, current_user: AdminUser, db: DBSession) -> EscalationPolicyResponse:
    svc = _svc(db)
    policy = await svc.create_policy(CreatePolicyCommand(
        org_id=current_user.org_id, name=body.name,
        trigger_after_hours=body.trigger_after_hours,
        levels=[lvl.model_dump() for lvl in body.levels],
        is_default=body.is_default,
    ))
    return map_policy(policy)


@router.get("/{policy_id}", response_model=EscalationPolicyResponse, summary="[Admin] Get policy")
async def get_policy(policy_id: uuid.UUID, current_user: AdminUser, db: DBSession) -> EscalationPolicyResponse:
    from app.domains.notifications.domain.exceptions import PolicyNotFoundError
    repo = SQLEscalationPolicyRepository(db)
    policy = await repo.get_by_id(policy_id, current_user.org_id)
    if not policy:
        raise PolicyNotFoundError()
    return map_policy(policy)


@router.put("/{policy_id}", response_model=EscalationPolicyResponse, summary="[Admin] Update policy")
async def update_policy(
    policy_id: uuid.UUID, body: UpdatePolicyRequest,
    current_user: AdminUser, db: DBSession,
) -> EscalationPolicyResponse:
    svc = _svc(db)
    policy = await svc.update_policy(UpdatePolicyCommand(
        policy_id=policy_id, org_id=current_user.org_id, name=body.name,
        trigger_after_hours=body.trigger_after_hours,
        levels=[lvl.model_dump() for lvl in body.levels] if body.levels else None,
        is_default=body.is_default,
    ))
    return map_policy(policy)
