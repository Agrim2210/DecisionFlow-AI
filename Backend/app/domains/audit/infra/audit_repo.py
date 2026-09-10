from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.audit.domain.entities import AuditLog
from app.domains.audit.domain.repositories import IAuditRepository
from app.domains.audit.infra.orm_models import AuditLogORM


def _to_entity(orm: AuditLogORM) -> AuditLog:
    return AuditLog(
        id=orm.id,
        org_id=orm.org_id,
        actor_id=orm.actor_id,
        actor_type=orm.actor_type,
        event_type=orm.event_type,
        aggregate_type=orm.aggregate_type,
        aggregate_id=orm.aggregate_id,
        before_state=dict(orm.before_state or {}),
        after_state=dict(orm.after_state or {}),
        ip_address=orm.ip_address,
        metadata=dict(orm.event_metadata or {}),
        occurred_at=orm.occurred_at,
    )


class SQLAuditRepository(IAuditRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def append(self, log: AuditLog) -> AuditLog:
        orm = AuditLogORM(
            id=log.id,
            org_id=log.org_id,
            actor_id=log.actor_id,
            actor_type=log.actor_type,
            event_type=log.event_type,
            aggregate_type=log.aggregate_type,
            aggregate_id=log.aggregate_id,
            before_state=log.before_state,
            after_state=log.after_state,
            ip_address=log.ip_address,
            event_metadata=log.metadata,
            occurred_at=log.occurred_at,
        )
        self._db.add(orm)
        await self._db.flush()
        return _to_entity(orm)

    async def get_by_id(
        self, log_id: uuid.UUID, org_id: uuid.UUID
    ) -> AuditLog | None:
        result = await self._db.execute(
            select(AuditLogORM).where(
                AuditLogORM.id == log_id,
                AuditLogORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list(
        self,
        org_id: uuid.UUID,
        limit: int = 20,
        cursor_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        aggregate_type: str | None = None,
        event_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AuditLog]:
        q = select(AuditLogORM).where(AuditLogORM.org_id == org_id)
        if actor_id:
            q = q.where(AuditLogORM.actor_id == actor_id)
        if aggregate_type:
            q = q.where(AuditLogORM.aggregate_type == aggregate_type)
        if event_type:
            q = q.where(AuditLogORM.event_type == event_type)
        if date_from:
            q = q.where(AuditLogORM.occurred_at >= date_from)
        if date_to:
            q = q.where(AuditLogORM.occurred_at <= date_to)
        if cursor_id:
            q = q.where(AuditLogORM.id < cursor_id)
        q = q.order_by(AuditLogORM.occurred_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_to_entity(r) for r in result.scalars().all()]
