   
from __future__ import annotations

import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, BackgroundTasks

from app.domains.identity.api.schemas import (
    ChangePasswordRequest,
    ChangeRoleRequest,
    InviteUserRequest,
    ListUsersRequest,   
    PendingUserListResponse,
    PendingUserResponse,
    UpdateProfileRequest,
    UserListResponse,
    RegistrationPendingResponse,
    UserResponse,
    map_user_to_response,
)
from app.domains.identity.application.commands import (
    ChangePasswordCommand,
    ChangeUserRoleCommand,
    DeactivateUserCommand,
    InviteUserCommand,
    UpdateProfileCommand,
)
from app.domains.identity.application.queries import (
    GetUserQuery,
    ListUsersQuery,
)
from app.domains.identity.application.user_service import UserService
from app.domains.identity.infra.repositories import (
    SQLOrganizationRepository,
    SQLPendingUserRepository,
    SQLRefreshTokenRepository,
    SQLUserRepository,
)
from app.shared.deps import AdminUser, CurrentUser, DBSession
from app.shared.pagination import decode_cursor
from app.shared.config import settings
from app.domains.notifications.infra.email_adapter import EmailAdapter

router = APIRouter(prefix="/users", tags=["Users"])


def _build_service(db) -> UserService:
    return UserService(
        user_repo=SQLUserRepository(db),
        org_repo=SQLOrganizationRepository(db),
        token_repo=SQLRefreshTokenRepository(db),
        pending_user_repo=SQLPendingUserRepository(db),
    )


                                                                    
@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users in the organization",
)
async def list_users(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 50,
    cursor: str | None = None,
    role: str | None = None,
) -> UserListResponse:
    cursor_id: uuid.UUID | None = None
    if cursor:
        try:
            cursor_id = decode_cursor(cursor)
        except ValueError:
            cursor_id = None

    service = _build_service(db)
    users = await service.list_users(
        ListUsersQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=cursor_id,
            role_filter=role,
        )
    )

    has_next = len(users) > limit
    page = users[:limit]

    from app.shared.pagination import encode_cursor
    return UserListResponse(
        users=[map_user_to_response(u) for u in page],
        has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


                                                                    
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user in the organization",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    service = _build_service(db)
    user = await service.get_user(
        GetUserQuery(user_id=user_id, org_id=current_user.org_id)
    )
    return map_user_to_response(user)


                                                                    
@router.post(
    "/invite",
    response_model=RegistrationPendingResponse,
    status_code=202,
    summary="[Admin] Invite a member and send an email verification link",
)
async def invite_user(
    body: InviteUserRequest,
    background_tasks: BackgroundTasks,
    current_user: AdminUser,
    db: DBSession,
) -> RegistrationPendingResponse:
    service = _build_service(db)
    result = await service.invite_user(
        InviteUserCommand(
            org_id=current_user.org_id,
            invited_by_user_id=current_user.id,
            email=body.email,
            name=body.name,
            role=body.role,
            temp_password=body.temp_password,
        )
    )
    await db.commit()
    verification_url = (
        f"{settings.API_PUBLIC_URL.rstrip('/')}/api/v1/identity/auth/verify-email?"
        f"{urlencode({'token': result.raw_verification_token})}"
    )
    background_tasks.add_task(
        EmailAdapter().send_invitation_verification_email,
        recipient_email=result.pending_user.email,
        recipient_name=result.pending_user.name,
        verification_url=verification_url,
    )
    return RegistrationPendingResponse(
        message="Invitation sent. The member must verify their email to activate access.",
        email=result.pending_user.email,
        verification_url=verification_url,
    )


                                                                    
@router.get(
    "/pending",
    response_model=PendingUserListResponse,
    summary="List all pending invitations in the organization",
)
async def list_pending_invitations(
    current_user: CurrentUser,
    db: DBSession,
) -> PendingUserListResponse:
    service = _build_service(db)
    pending_users = await service.list_pending_invitations(current_user.org_id)
    return PendingUserListResponse(
        invitations=[
            PendingUserResponse(
                id=p.id,
                email=p.email,
                name=p.name,
                invited_role=p.invited_role or "member",
                verification_expires_at=p.verification_expires_at.isoformat(),
                created_at=p.created_at.isoformat(),
            )
            for p in pending_users
        ]
    )


                                                                    
@router.delete(
    "/pending/{pending_id}",
    status_code=204,
    summary="[Admin] Revoke/cancel a pending invitation",
)
async def cancel_pending_invitation(
    pending_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> None:
    service = _build_service(db)
    await service.cancel_invitation(pending_id, current_user.org_id)
    await db.commit()


                                                                    
@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="[Admin] Change a user's role",
)
async def change_role(
    user_id: uuid.UUID,
    body: ChangeRoleRequest,
    current_user: AdminUser,
    db: DBSession,
) -> UserResponse:
    service = _build_service(db)
    user = await service.change_user_role(
        ChangeUserRoleCommand(
            org_id=current_user.org_id,
            target_user_id=user_id,
            new_role=body.role,
            changed_by_user_id=current_user.id,
        )
    )
    return map_user_to_response(user)


                                                                    
@router.delete(
    "/{user_id}",
    status_code=204,
    summary="[Admin] Deactivate a user account",
)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> None:
    service = _build_service(db)
    await service.deactivate_user(
        DeactivateUserCommand(
            org_id=current_user.org_id,
            target_user_id=user_id,
            requested_by_user_id=current_user.id,
        )
    )


                                                                    
@router.patch(
    "/me/profile",
    response_model=UserResponse,
    summary="Update your own profile (name, avatar)",
)
async def update_my_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> UserResponse:
    service = _build_service(db)
    user = await service.update_profile(
        UpdateProfileCommand(
            user_id=current_user.id,
            org_id=current_user.org_id,
            name=body.name,
            avatar_url=body.avatar_url,
        )
    )
    return map_user_to_response(user)


                                                                    
@router.post(
    "/me/change-password",
    status_code=204,
    summary="Change your own password (invalidates all other sessions)",
)
async def change_my_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    service = _build_service(db)
    await service.change_password(
        ChangePasswordCommand(
            user_id=current_user.id,
            org_id=current_user.org_id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    )
