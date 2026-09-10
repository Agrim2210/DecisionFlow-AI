   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import structlog

from app.domains.identity.application.commands import (
    LoginCommand,
    LogoutCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    RefreshTokensCommand,
    RegisterOrgCommand,
)
from app.domains.identity.domain.entities import Organization, RefreshToken, User
from app.domains.identity.domain.entities import PendingUser
from app.domains.identity.domain.exceptions import (
    EmailAlreadyRegisteredError,
    OrgSlugTakenError,
)
from app.domains.identity.domain.repositories import (
    IOrganizationRepository,
    IPendingUserRepository,
    IRefreshTokenRepository,
    IUserRepository,
)
from app.domains.identity.domain.value_objects import PasswordPolicy
from app.shared.config import settings
from app.shared.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    RefreshTokenReuseError,
    TokenExpiredError,
    TokenRevokedError,
    UserInactiveError,
)
from app.shared.security import (
    create_access_token,
    generate_refresh_token,
    generate_one_time_token,
    generate_email_verification_token,
    hash_email_verification_token,
    email_verification_expiry,
    hash_password,
    hash_refresh_token,
    hash_one_time_token,
    invitation_token_expiry,
    one_time_token_expiry,
    refresh_token_expiry,
    verify_password,
)

logger = structlog.get_logger(__name__)


@dataclass
class AuthResult:
                                                                                  
    user: User
    organization: Organization
    access_token: str
    raw_refresh_token: str                                    


@dataclass
class RefreshResult:
                                    
    user: User
    organization: Organization
    access_token: str
    raw_refresh_token: str


@dataclass
class PendingRegistrationResult:
    pending_user: PendingUser
    raw_verification_token: str


@dataclass
class EmailVerificationResult:
    status: str                                                               
    raw_password_reset_token: str | None = None


@dataclass
class PasswordResetRequestResult:
    user: User | None
    raw_token: str | None


@dataclass
class PasswordResetResult:
    status: str                   


class AuthService:
       

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

                                                                    
    async def register_org(self, cmd: RegisterOrgCommand) -> PendingRegistrationResult:
           
                                                     
        PasswordPolicy.validate(cmd.password)

                                         
        if await self._orgs.slug_exists(cmd.org_slug):
            raise OrgSlugTakenError(
                f"The slug '{cmd.org_slug}' is already taken."
            )
        if await self._pending_users.slug_exists(cmd.org_slug):
            raise OrgSlugTakenError(
                f"The slug '{cmd.org_slug}' has a registration awaiting email verification."
            )
        if await self._users.email_exists(cmd.email):
            raise EmailAlreadyRegisteredError(
                f"An account with '{cmd.email}' already exists."
            )
        if await self._pending_users.email_exists(cmd.email):
            raise EmailAlreadyRegisteredError(
                f"A verification request for '{cmd.email}' already exists. Check your inbox."
            )

        raw_token, token_hash = generate_email_verification_token()
        pending_user = PendingUser(
            id=uuid.uuid4(),
            org_name=cmd.org_name,
            org_slug=cmd.org_slug,
            email=cmd.email,
            name=cmd.user_name,
            hashed_password=hash_password(cmd.password),
            verification_token_hash=token_hash,
            verification_expires_at=email_verification_expiry(),
        )
        pending_user = await self._pending_users.create(pending_user)

        logger.info(
            "registration_pending_verification", email=pending_user.email,
            org_slug=pending_user.org_slug,
        )

                                                               
                                                                               
                                                                                   

        return PendingRegistrationResult(pending_user=pending_user, raw_verification_token=raw_token)

    async def verify_email(self, raw_token: str) -> EmailVerificationResult:
                                                                                       
        token_hash = hash_email_verification_token(raw_token)
        pending = await self._pending_users.get_by_token_hash(token_hash)
        now = datetime.now(timezone.utc)
        if not pending:
            user = await self._users.get_by_email_verification_token(token_hash)
            if user and user.is_email_verified:
                return EmailVerificationResult(status="already_verified")
            return EmailVerificationResult(status="expired")
        if pending.verification_expires_at <= now:
            await self._pending_users.delete(pending.id)
            return EmailVerificationResult(status="expired")
        if pending.invited_org_id:
            if await self._users.email_exists(pending.email):
                raise EmailAlreadyRegisteredError("This invitation can no longer be verified")
            org = await self._orgs.get_by_id(pending.invited_org_id)
            if not org:
                await self._pending_users.delete(pending.id)
                return EmailVerificationResult(status="expired")
            current_count = await self._orgs.count_active_users(org.id)
            if not org.can_add_user(current_count):
                return EmailVerificationResult(status="expired")
            raw_reset_token, reset_token_hash = generate_one_time_token()
            user = await self._users.create(User(
                id=uuid.uuid4(), org_id=org.id, email=pending.email, name=pending.name,
                hashed_password=pending.hashed_password, role=pending.invited_role or "member",
                is_active=True, is_email_verified=True,
                email_verification_token=token_hash,
                email_verification_expires_at=pending.verification_expires_at,
                password_reset_token_hash=reset_token_hash,
                password_reset_expires_at=invitation_token_expiry(),
            ))
            await self._pending_users.delete(pending.id)
            logger.info(
                "invitation_verified_user_created", user_id=str(user.id), org_id=str(org.id),
                role=user.role,
            )
            return EmailVerificationResult(
                status="invitation_verified", raw_password_reset_token=raw_reset_token
            )
        if await self._users.email_exists(pending.email) or await self._orgs.slug_exists(pending.org_slug):
            raise EmailAlreadyRegisteredError("This registration can no longer be verified")
        org = await self._orgs.create(Organization(
            id=uuid.uuid4(), name=pending.org_name, slug=pending.org_slug, plan="starter",
            settings={}, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)))
        user = await self._users.create(User(
            id=uuid.uuid4(), org_id=org.id, email=pending.email, name=pending.name,
            hashed_password=pending.hashed_password, role="owner", is_active=True,
            is_email_verified=True, email_verification_token=token_hash,
            email_verification_expires_at=pending.verification_expires_at))
        await self._pending_users.delete(pending.id)
        logger.info("email_verified_org_created", user_id=str(user.id), org_id=str(org.id))
        return EmailVerificationResult(status="verified")

    async def request_password_reset(self, cmd: RequestPasswordResetCommand) -> PasswordResetRequestResult:
                                                                                                   
        user = await self._users.get_by_email(cmd.email)
        if not user or not user.is_active:
            return PasswordResetRequestResult(user=None, raw_token=None)
        raw_token, token_hash = generate_one_time_token()
        user.password_reset_token_hash = token_hash
        user.password_reset_expires_at = one_time_token_expiry(settings.PASSWORD_RESET_TTL_MINUTES)
        user.password_reset_used_at = None
        user = await self._users.update(user)
        logger.info("password_reset_requested", user_id=str(user.id))
        return PasswordResetRequestResult(user=user, raw_token=raw_token)

    async def validate_password_reset_token(self, raw_token: str) -> str:
                                                                                
        token_hash = hash_one_time_token(raw_token)
        user = await self._users.get_by_password_reset_token(token_hash)
        now = datetime.now(timezone.utc)
        if (
            not user
            or not user.password_reset_expires_at
            or user.password_reset_expires_at <= now
            or user.password_reset_used_at is not None
        ):
            return "expired"
        return "valid"

    async def reset_password(self, cmd: ResetPasswordCommand) -> PasswordResetResult:
        token_hash = hash_one_time_token(cmd.raw_token)
        user = await self._users.get_by_password_reset_token(token_hash)
        now = datetime.now(timezone.utc)
        if (
            not user
            or not user.password_reset_expires_at
            or user.password_reset_expires_at <= now
            or user.password_reset_used_at is not None
        ):
            return PasswordResetResult(status="expired")
        PasswordPolicy.validate(cmd.new_password)
        user.hashed_password = hash_password(cmd.new_password)
        user.password_reset_used_at = now
        await self._users.update(user)
        await self._tokens.revoke_all_for_user(user.id)
        logger.info("password_reset_completed", user_id=str(user.id))
        return PasswordResetResult(status="reset")

                                                                    
    async def login(self, cmd: LoginCommand) -> AuthResult:
           
        user = await self._users.get_by_email(cmd.email)

                                                                   
        password_ok = verify_password(
            cmd.password,
            user.hashed_password if user else None,
        )

        if not user or not password_ok:
            logger.warning("login_failed", email=cmd.email, ip=cmd.ip_address)
            raise InvalidCredentialsError()

        if not user.is_active:
            raise UserInactiveError()

                                                
        org = await self._orgs.get_by_id(user.org_id)
        if org is None:
            raise AuthenticationError("Organization not found")

                      
        access_token = create_access_token(
            user_id=user.id,
            org_id=user.org_id,
            role=user.role,
            plan=org.plan,
        )
        raw_refresh, hashed_refresh = generate_refresh_token()
        refresh_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hashed_refresh,
            family_id=uuid.uuid4(),                             
            expires_at=refresh_token_expiry(),
            created_at=datetime.now(timezone.utc),
            ip_address=cmd.ip_address,
            user_agent=cmd.user_agent,
        )
        await self._tokens.create(refresh_token)

                                                                    
        now = datetime.now(timezone.utc)
        user = User(
            **{**user.__dict__, "last_login_at": now, "last_active_at": now}
        )
        await self._users.update(user)

        logger.info(
            "login_success",
            user_id=str(user.id),
            org_id=str(user.org_id),
            ip=cmd.ip_address,
        )

        return AuthResult(
            user=user,
            organization=org,
            access_token=access_token,
            raw_refresh_token=raw_refresh,
        )

                                                                    
    async def refresh_tokens(self, cmd: RefreshTokensCommand) -> RefreshResult:
           
        token_hash = hash_refresh_token(cmd.raw_refresh_token)
        stored_token = await self._tokens.get_by_hash(token_hash)

        if not stored_token:
            raise TokenRevokedError("Refresh token not found")

                                                     
        if stored_token.is_used:
            logger.error(
                "refresh_token_reuse",
                token_id=str(stored_token.id),
                user_id=str(stored_token.user_id),
                family_id=str(stored_token.family_id),
                ip=cmd.ip_address,
            )
                                                                          
            revoked_count = await self._tokens.revoke_family(stored_token.family_id)
            logger.warning(
                "token_family_revoked",
                family_id=str(stored_token.family_id),
                revoked_count=revoked_count,
            )
            raise RefreshTokenReuseError()

        if stored_token.is_revoked:
            raise TokenRevokedError()

        if stored_token.is_expired:
            raise TokenExpiredError("Refresh token has expired. Please log in again.")

                         
        now = datetime.now(timezone.utc)
        user = await self._users.get_by_email_from_id(stored_token.user_id)                              
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        org = await self._orgs.get_by_id(user.org_id)
        if not org:
            raise AuthenticationError("Organization not found")

                                
        await self._tokens.mark_used(stored_token.id, now)

                                                                     
        new_access = create_access_token(
            user_id=user.id,
            org_id=user.org_id,
            role=user.role,
            plan=org.plan,
        )
        new_raw, new_hash = generate_refresh_token()
        new_token = RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=new_hash,
            family_id=stored_token.family_id,                
            expires_at=refresh_token_expiry(),
            created_at=now,
            ip_address=cmd.ip_address,
        )
        await self._tokens.create(new_token)

        logger.info("tokens_refreshed", user_id=str(user.id))

        return RefreshResult(
            user=user,
            organization=org,
            access_token=new_access,
            raw_refresh_token=new_raw,
        )

                                                                    
    async def logout(self, cmd: LogoutCommand) -> None:
                                                                           
        if cmd.logout_all:
            count = await self._tokens.revoke_all_for_user(cmd.user_id)
            logger.info("logout_all", user_id=str(cmd.user_id), tokens_revoked=count)
            return

        if cmd.raw_refresh_token:
            token_hash = hash_refresh_token(cmd.raw_refresh_token)
            stored = await self._tokens.get_by_hash(token_hash)
            if stored and not stored.is_revoked:
                await self._tokens.revoke_by_id(stored.id)
                logger.info("logout", user_id=str(cmd.user_id))
