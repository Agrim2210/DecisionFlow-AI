   
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.identity.domain.entities import Organization, PendingUser, RefreshToken, User
from app.domains.identity.domain.repositories import (
    IOrganizationRepository,
    IPendingUserRepository,
    IRefreshTokenRepository,
    IUserRepository,
)
from app.domains.identity.infra.orm_models import (
    OrganizationORM,
    PendingUserORM,
    RefreshTokenORM,
    UserORM,
)


def _pending_user_to_entity(orm: PendingUserORM) -> PendingUser:
    return PendingUser(id=orm.id, org_name=orm.org_name, org_slug=orm.org_slug,
        email=orm.email, name=orm.name, hashed_password=orm.hashed_password,
        verification_token_hash=orm.verification_token_hash,
        verification_expires_at=orm.verification_expires_at,
        invited_org_id=orm.invited_org_id, invited_role=orm.invited_role,
        invited_by_user_id=orm.invited_by_user_id, created_at=orm.created_at,
        updated_at=orm.updated_at)


                                                                     
def _org_to_entity(orm: OrganizationORM) -> Organization:
    return Organization(
        id=orm.id,
        name=orm.name,
        slug=orm.slug,
        plan=orm.plan,
        settings=orm.settings or {},
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )


def _user_to_entity(orm: UserORM) -> User:
    return User(
        id=orm.id,
        org_id=orm.org_id,
        email=orm.email,
        name=orm.name,
        hashed_password=orm.hashed_password,
        role=orm.role,
        is_active=orm.is_active,
        is_email_verified=orm.is_email_verified,
        avatar_url=orm.avatar_url,
        email_verification_token=orm.email_verification_token,
        email_verification_expires_at=orm.email_verification_expires_at,
        password_reset_token_hash=orm.password_reset_token_hash,
        password_reset_expires_at=orm.password_reset_expires_at,
        password_reset_used_at=orm.password_reset_used_at,
        reliability_score=float(orm.reliability_score),
        last_active_at=orm.last_active_at,
        last_login_at=orm.last_login_at,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )


def _token_to_entity(orm: RefreshTokenORM) -> RefreshToken:
    return RefreshToken(
        id=orm.id,
        user_id=orm.user_id,
        token_hash=orm.token_hash,
        family_id=orm.family_id,
        expires_at=orm.expires_at,
        is_used=orm.is_used,
        is_revoked=orm.is_revoked,
        created_at=orm.created_at,
        used_at=orm.used_at,
        ip_address=orm.ip_address,
        user_agent=orm.user_agent,
    )


                                                                     
class SQLOrganizationRepository(IOrganizationRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, org: Organization) -> Organization:
        orm = OrganizationORM(
            id=org.id,
            name=org.name,
            slug=org.slug,
            plan=org.plan,
            settings=org.settings,
        )
        self._db.add(orm)
        await self._db.flush()                                                  
        await self._db.refresh(orm)
        return _org_to_entity(orm)

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        result = await self._db.execute(
            select(OrganizationORM).where(
                OrganizationORM.id == org_id,
                OrganizationORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _org_to_entity(orm) if orm else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._db.execute(
            select(OrganizationORM).where(
                OrganizationORM.slug == slug,
                OrganizationORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _org_to_entity(orm) if orm else None

    async def update(self, org: Organization) -> Organization:
        result = await self._db.execute(
            select(OrganizationORM).where(OrganizationORM.id == org.id)
        )
        orm = result.scalar_one()
        orm.name = org.name
        orm.plan = org.plan
        orm.settings = org.settings
        orm.deleted_at = org.deleted_at
        await self._db.flush()
        await self._db.refresh(orm)
        return _org_to_entity(orm)

    async def slug_exists(self, slug: str) -> bool:
        result = await self._db.execute(
            select(OrganizationORM.id).where(
                OrganizationORM.slug == slug,
                OrganizationORM.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_active_users(self, org_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self._db.execute(
            select(func.count(UserORM.id)).where(
                UserORM.org_id == org_id,
                UserORM.is_active.is_(True),
                UserORM.deleted_at.is_(None),
            )
        )
        return result.scalar_one() or 0


                                                                     
class SQLUserRepository(IUserRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, user: User) -> User:
        orm = UserORM(
            id=user.id,
            org_id=user.org_id,
            email=user.email,
            name=user.name,
            hashed_password=user.hashed_password,
            role=user.role,
            is_active=user.is_active,
            is_email_verified=user.is_email_verified,
            avatar_url=user.avatar_url,
            email_verification_token=user.email_verification_token,
            email_verification_expires_at=user.email_verification_expires_at,
            password_reset_token_hash=user.password_reset_token_hash,
            password_reset_expires_at=user.password_reset_expires_at,
            password_reset_used_at=user.password_reset_used_at,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _user_to_entity(orm)

    async def get_by_id(self, user_id: uuid.UUID, org_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.id == user_id,
                UserORM.org_id == org_id,
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.email == email.lower().strip(),
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None

    async def get_by_email_verification_token(self, token_hash: str) -> User | None:
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.email_verification_token == token_hash,
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None

    async def get_by_password_reset_token(self, token_hash: str) -> User | None:
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.password_reset_token_hash == token_hash,
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None

    async def get_by_email_in_org(self, email: str, org_id: uuid.UUID) -> User | None:
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.email == email.lower().strip(),
                UserORM.org_id == org_id,
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
    ) -> list[User]:
        query = select(UserORM).where(
            UserORM.org_id == org_id,
            UserORM.deleted_at.is_(None),
        )
        if cursor_id:
            query = query.where(UserORM.id > cursor_id)
        query = query.order_by(UserORM.created_at.asc()).limit(limit)
        result = await self._db.execute(query)
        return [_user_to_entity(row) for row in result.scalars().all()]

    async def update(self, user: User) -> User:
        result = await self._db.execute(
            select(UserORM).where(UserORM.id == user.id)
        )
        orm = result.scalar_one()
        orm.name = user.name
        orm.email = user.email
        orm.role = user.role
        orm.is_active = user.is_active
        orm.is_email_verified = user.is_email_verified
        orm.avatar_url = user.avatar_url
        orm.email_verification_token = user.email_verification_token
        orm.email_verification_expires_at = user.email_verification_expires_at
        orm.password_reset_token_hash = user.password_reset_token_hash
        orm.password_reset_expires_at = user.password_reset_expires_at
        orm.password_reset_used_at = user.password_reset_used_at
        orm.hashed_password = user.hashed_password
        orm.last_login_at = user.last_login_at
        orm.last_active_at = user.last_active_at
        orm.deleted_at = user.deleted_at
        await self._db.flush()
        await self._db.refresh(orm)
        return _user_to_entity(orm)

    async def email_exists(self, email: str) -> bool:
        result = await self._db.execute(
            select(UserORM.id).where(
                UserORM.email == email.lower().strip(),
                UserORM.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None

    async def update_last_active(self, user_id: uuid.UUID, at: datetime) -> None:
        await self._db.execute(
            update(UserORM)
            .where(UserORM.id == user_id)
            .values(last_active_at=at)
        )


class SQLPendingUserRepository(IPendingUserRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, pending_user: PendingUser) -> PendingUser:
        orm = PendingUserORM(
            id=pending_user.id, org_name=pending_user.org_name, org_slug=pending_user.org_slug,
            email=pending_user.email, name=pending_user.name,
            hashed_password=pending_user.hashed_password,
            verification_token_hash=pending_user.verification_token_hash,
            verification_expires_at=pending_user.verification_expires_at,
            invited_org_id=pending_user.invited_org_id,
            invited_role=pending_user.invited_role,
            invited_by_user_id=pending_user.invited_by_user_id,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _pending_user_to_entity(orm)

    async def get_by_token_hash(self, token_hash: str) -> PendingUser | None:
        result = await self._db.execute(select(PendingUserORM).where(
            PendingUserORM.verification_token_hash == token_hash))
        orm = result.scalar_one_or_none()
        return _pending_user_to_entity(orm) if orm else None

    async def get_by_email(self, email: str) -> PendingUser | None:
        result = await self._db.execute(select(PendingUserORM).where(
            PendingUserORM.email == email.lower().strip()))
        orm = result.scalar_one_or_none()
        return _pending_user_to_entity(orm) if orm else None

    async def list_by_org(self, org_id: uuid.UUID) -> list[PendingUser]:
        result = await self._db.execute(
            select(PendingUserORM)
            .where(PendingUserORM.invited_org_id == org_id)
            .order_by(PendingUserORM.created_at.desc())
        )
        return [_pending_user_to_entity(row) for row in result.scalars().all()]

    async def update(self, pending_user: PendingUser) -> PendingUser:
        result = await self._db.execute(
            select(PendingUserORM).where(PendingUserORM.id == pending_user.id)
        )
        orm = result.scalar_one()
        orm.name = pending_user.name
        orm.hashed_password = pending_user.hashed_password
        orm.verification_token_hash = pending_user.verification_token_hash
        orm.verification_expires_at = pending_user.verification_expires_at
        orm.invited_role = pending_user.invited_role
        orm.invited_by_user_id = pending_user.invited_by_user_id
        await self._db.flush()
        await self._db.refresh(orm)
        return _pending_user_to_entity(orm)

    async def email_exists(self, email: str) -> bool:
        result = await self._db.execute(select(PendingUserORM.id).where(
            PendingUserORM.email == email.lower().strip()))
        return result.scalar_one_or_none() is not None

    async def slug_exists(self, slug: str) -> bool:
        result = await self._db.execute(select(PendingUserORM.id).where(
            PendingUserORM.org_slug == slug.lower().strip()))
        return result.scalar_one_or_none() is not None

    async def delete(self, pending_user_id: uuid.UUID) -> None:
        await self._db.execute(
            PendingUserORM.__table__.delete().where(PendingUserORM.id == pending_user_id)
        )


                                                                      
class SQLRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, token: RefreshToken) -> RefreshToken:
        orm = RefreshTokenORM(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            family_id=token.family_id,
            expires_at=token.expires_at,
            created_at=token.created_at,
            ip_address=token.ip_address,
            user_agent=token.user_agent,
        )
        self._db.add(orm)
        await self._db.flush()
        return _token_to_entity(orm)

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self._db.execute(
            select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
        )
        orm = result.scalar_one_or_none()
        return _token_to_entity(orm) if orm else None

    async def mark_used(self, token_id: uuid.UUID, used_at: datetime) -> None:
        await self._db.execute(
            update(RefreshTokenORM)
            .where(RefreshTokenORM.id == token_id)
            .values(is_used=True, used_at=used_at)
        )

    async def revoke_by_id(self, token_id: uuid.UUID) -> None:
        await self._db.execute(
            update(RefreshTokenORM)
            .where(RefreshTokenORM.id == token_id)
            .values(is_revoked=True)
        )

    async def revoke_family(self, family_id: uuid.UUID) -> int:
        result = await self._db.execute(
            update(RefreshTokenORM)
            .where(
                RefreshTokenORM.family_id == family_id,
                RefreshTokenORM.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        return result.rowcount                              

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> int:
        result = await self._db.execute(
            update(RefreshTokenORM)
            .where(
                RefreshTokenORM.user_id == user_id,
                RefreshTokenORM.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        return result.rowcount                              


    async def get_by_email_from_id(self, user_id) -> "User | None":
                                                                     
        result = await self._db.execute(
            select(UserORM).where(
                UserORM.id == user_id,
                UserORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _user_to_entity(orm) if orm else None
