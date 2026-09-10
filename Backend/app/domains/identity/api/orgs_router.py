   
from __future__ import annotations

from fastapi import APIRouter

from app.domains.identity.api.schemas import (
    OrgResponse,
    UpdateOrgSettingsRequest,
    map_org_to_response,
)
from app.domains.identity.application.commands import UpdateOrgSettingsCommand
from app.domains.identity.application.queries import GetOrgQuery
from app.domains.identity.application.user_service import UserService
from app.domains.identity.infra.repositories import (
    SQLOrganizationRepository,
    SQLPendingUserRepository,
    SQLRefreshTokenRepository,
    SQLUserRepository,
)
from app.shared.deps import CurrentUser, DBSession, OwnerUser

router = APIRouter(prefix="/orgs", tags=["Organizations"])


def _build_service(db) -> UserService:
    return UserService(
        user_repo=SQLUserRepository(db),
        org_repo=SQLOrganizationRepository(db),
        token_repo=SQLRefreshTokenRepository(db),
        pending_user_repo=SQLPendingUserRepository(db),
    )


@router.get(
    "/me",
    response_model=OrgResponse,
    summary="Get current organization details",
)
async def get_my_org(
    current_user=CurrentUser,
    db=DBSession,
) -> OrgResponse:
    service = _build_service(db)
    org = await service.get_org(GetOrgQuery(org_id=current_user.org_id))
    return map_org_to_response(org)


@router.patch(
    "/me",
    response_model=OrgResponse,
    summary="[Owner] Update organization name or settings",
)
async def update_org_settings(
    body: UpdateOrgSettingsRequest,
    current_user=OwnerUser,
    db=DBSession,
) -> OrgResponse:
    service = _build_service(db)
    org = await service.update_org_settings(
        UpdateOrgSettingsCommand(
            org_id=current_user.org_id,
            requested_by_user_id=current_user.id,
            name=body.name,
            settings=body.settings,
        )
    )
    return map_org_to_response(org)
