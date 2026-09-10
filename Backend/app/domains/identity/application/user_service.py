   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import structlog

from app.domains.identity.application.commands import (
    ChangePasswordCommand,
    ChangeUserRoleCommand,
    DeactivateUserCommand,
    InviteUserCommand,
    UpdateOrgSettingsCommand,
    UpdateProfileCommand,
)
from app.domains.identity.application.queries import (
    GetMeQuery,
    GetOrgQuery,
    GetUserQuery,
    ListUsersQuery,
)
from app.domains.identity.domain.entities import Organization, PendingUser, User
from app.domains.identity.domain.exceptions import (
    CannotChangeOwnerRoleError,
    CannotDeactivateOwnerError,
    CannotDeactivateSelfError,
    EmailAlreadyRegisteredError,
    OrgUserLimitExceededError,
    UserNotFoundError,
)
from app.domains.identity.domain.repositories import (
    IOrganizationRepository,
    IPendingUserRepository,
    IRefreshTokenRepository,
    IUserRepository,
)
from app.domains.identity.domain.value_objects import PasswordPolicy
from app.shared.exceptions import (
    InvalidCredentialsError,
    NotFoundError,
    PermissionDeniedError,
)
from app.shared.security import (
    email_verification_expiry,
    generate_email_verification_token,
    hash_password,
    invitation_token_expiry,
    verify_password,
)

logger = structlog.get_logger(__name__)


@dataclass
class PendingInvitationResult:
    pending_user: PendingUser
    raw_verification_token: str


class UserService:
    def __init__(
        self,
        user_repo: IUserRepository,
        org_repo: IOrganizationRepository,
        token_repo: IRefreshTokenRepository,
        pending_user_repo: IPendingUserRepository,
    ) -> None:
        self._users = user_repo
        self._orgs = org_repo
        self._tokens = token_repo
        self._pending_users = pending_user_repo

                                                                    
    async def get_me(self, query: GetMeQuery) -> tuple[User, Organization]:
                                                       
        user = await self._users.get_by_id(query.user_id, query.org_id)
        if not user:
            raise UserNotFoundError()

        org = await self._orgs.get_by_id(query.org_id)
        if not org:
            raise NotFoundError("Organization not found")

        return user, org

    async def get_user(self, query: GetUserQuery) -> User:
                                                               
        user = await self._users.get_by_id(query.user_id, query.org_id)
        if not user:
            raise UserNotFoundError(f"User {query.user_id} not found in this organization")
        return user

    async def list_users(self, query: ListUsersQuery) -> list[User]:
                                                    
        users = await self._users.list_by_org(
            org_id=query.org_id,
            limit=query.limit + 1,                                 
            cursor_id=query.cursor_id,
        )
                                                             
        if query.role_filter:
            users = [u for u in users if u.role == query.role_filter]
        if query.active_only:
            users = [u for u in users if u.is_active and not u.is_deleted]
        return users

    async def get_org(self, query: GetOrgQuery) -> Organization:
                                         
        org = await self._orgs.get_by_id(query.org_id)
        if not org:
            raise NotFoundError("Organization not found")
        return org

                                                                    
    async def invite_user(self, cmd: InviteUserCommand) -> PendingInvitationResult:
           
                          
        org = await self._orgs.get_by_id(cmd.org_id)
        if not org:
            raise NotFoundError("Organization not found")

        current_count = await self._orgs.count_active_users(cmd.org_id)
        if not org.can_add_user(current_count):
            raise OrgUserLimitExceededError(
                f"Your {org.plan} plan allows {org.max_users} users. "
                f"You currently have {current_count}. Please upgrade."
            )

                                             
        if cmd.role == "owner":
            raise PermissionDeniedError("Cannot invite a user with the 'owner' role")

                                
        if await self._users.email_exists(cmd.email):
            raise EmailAlreadyRegisteredError(
                f"'{cmd.email}' already has an account. "
                "They can be added to your org via SSO (enterprise) or contact support."
            )

        PasswordPolicy.validate(cmd.temp_password)

        raw_token, token_hash = generate_email_verification_token()
        existing_pending = await self._pending_users.get_by_email(cmd.email)

        if existing_pending:
            pending_user = PendingUser(
                id=existing_pending.id,
                org_name=None,
                org_slug=None,
                email=cmd.email,
                name=cmd.name or existing_pending.name,
                hashed_password=hash_password(cmd.temp_password),
                verification_token_hash=token_hash,
                verification_expires_at=invitation_token_expiry(),
                invited_org_id=cmd.org_id,
                invited_role=cmd.role,
                invited_by_user_id=cmd.invited_by_user_id,
            )
            pending_user = await self._pending_users.update(pending_user)
            logger.info(
                "user_invitation_refreshed",
                org_id=str(cmd.org_id),
                pending_invitation_id=str(pending_user.id),
                role=cmd.role,
                invited_by=str(cmd.invited_by_user_id),
            )
        else:
            pending_user = PendingUser(
                id=uuid.uuid4(),
                org_name=None,
                org_slug=None,
                email=cmd.email,
                name=cmd.name,
                hashed_password=hash_password(cmd.temp_password),
                verification_token_hash=token_hash,
                verification_expires_at=invitation_token_expiry(),
                invited_org_id=cmd.org_id,
                invited_role=cmd.role,
                invited_by_user_id=cmd.invited_by_user_id,
            )
            pending_user = await self._pending_users.create(pending_user)
            logger.info(
                "user_invited",
                org_id=str(cmd.org_id),
                pending_invitation_id=str(pending_user.id),
                role=cmd.role,
                invited_by=str(cmd.invited_by_user_id),
            )

        return PendingInvitationResult(
            pending_user=pending_user,
            raw_verification_token=raw_token,
        )

    async def list_pending_invitations(self, org_id: uuid.UUID) -> list[PendingUser]:
        return await self._pending_users.list_by_org(org_id)

    async def cancel_invitation(self, pending_user_id: uuid.UUID, org_id: uuid.UUID) -> None:
        await self._pending_users.delete(pending_user_id)

                                                                    
    async def change_user_role(self, cmd: ChangeUserRoleCommand) -> User:
           
        target = await self._users.get_by_id(cmd.target_user_id, cmd.org_id)
        if not target:
            raise UserNotFoundError()

        if target.role == "owner":
            raise CannotChangeOwnerRoleError()

        if cmd.new_role == "owner":
            raise PermissionDeniedError(
                "Cannot assign 'owner' role. Use the ownership transfer endpoint."
            )

                      
        updated = User(**{**target.__dict__, "role": cmd.new_role})
        updated = await self._users.update(updated)

        logger.info(
            "role_changed",
            org_id=str(cmd.org_id),
            target_user_id=str(cmd.target_user_id),
            old_role=target.role,
            new_role=cmd.new_role,
            changed_by=str(cmd.changed_by_user_id),
        )

                                             

        return updated

                                                                    
    async def deactivate_user(self, cmd: DeactivateUserCommand) -> User:
           
        if cmd.target_user_id == cmd.requested_by_user_id:
            raise CannotDeactivateSelfError()

        target = await self._users.get_by_id(cmd.target_user_id, cmd.org_id)
        if not target:
            raise UserNotFoundError()

        if target.role == "owner":
            raise CannotDeactivateOwnerError()

                    
        updated = User(**{**target.__dict__, "is_active": False})
        updated = await self._users.update(updated)

                                                       
        revoked = await self._tokens.revoke_all_for_user(cmd.target_user_id)

        logger.info(
            "user_deactivated",
            org_id=str(cmd.org_id),
            target_user_id=str(cmd.target_user_id),
            tokens_revoked=revoked,
            requested_by=str(cmd.requested_by_user_id),
        )

        return updated

                                                                    
    async def update_profile(self, cmd: UpdateProfileCommand) -> User:
                                                  
        user = await self._users.get_by_id(cmd.user_id, cmd.org_id)
        if not user:
            raise UserNotFoundError()

        updates = {}
        if cmd.name is not None:
            updates["name"] = cmd.name.strip()
        if cmd.avatar_url is not None:
            updates["avatar_url"] = cmd.avatar_url

        if not updates:
            return user                     

        updated = User(**{**user.__dict__, **updates})
        return await self._users.update(updated)

                                                                    
    async def change_password(self, cmd: ChangePasswordCommand) -> None:
           
        user = await self._users.get_by_id(cmd.user_id, cmd.org_id)
        if not user:
            raise UserNotFoundError()

        if not verify_password(cmd.current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")

        PasswordPolicy.validate(cmd.new_password)

        updated = User(
            **{**user.__dict__, "hashed_password": hash_password(cmd.new_password)}
        )
        await self._users.update(updated)

                                                                   
        await self._tokens.revoke_all_for_user(cmd.user_id)

        logger.info("password_changed", user_id=str(cmd.user_id))

                                                                    
    async def update_org_settings(self, cmd: UpdateOrgSettingsCommand) -> Organization:
                                                  
        org = await self._orgs.get_by_id(cmd.org_id)
        if not org:
            raise NotFoundError("Organization not found")

        updates = {}
        if cmd.name is not None:
            updates["name"] = cmd.name.strip()
        if cmd.settings is not None:
                                                                   
            updates["settings"] = {**org.settings, **cmd.settings}

        if not updates:
            return org

        updated = Organization(**{**org.__dict__, **updates})
        updated = await self._orgs.update(updated)

        logger.info("org_settings_updated", org_id=str(cmd.org_id))
        return updated
