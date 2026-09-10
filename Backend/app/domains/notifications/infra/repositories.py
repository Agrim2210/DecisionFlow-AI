   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notifications.domain.entities import (
    Escalation,
    EscalationPolicy,
    EscalationStatus,
    Notification,
    NotifStatus,
)
from app.domains.notifications.domain.repositories import (
    IEscalationPolicyRepository,
    IEscalationRepository,
    INotificationRepository,
)
from app.domains.notifications.infra.orm_models import (
    EscalationORM,
    EscalationPolicyORM,
    NotificationORM,
)


                                                                     

def _notif_to_entity(orm: NotificationORM) -> Notification:
    return Notification(
        id=orm.id, org_id=orm.org_id, recipient_id=orm.recipient_id,
        event_type=orm.event_type, channel=orm.channel, status=orm.status,
        subject=orm.subject, body=orm.body,
        related_item_id=orm.related_item_id, related_item_type=orm.related_item_type,
        payload=orm.payload or {},
        sent_at=orm.sent_at, read_at=orm.read_at, failed_reason=orm.failed_reason,
        created_at=orm.created_at, updated_at=orm.updated_at,
    )


def _policy_to_entity(orm: EscalationPolicyORM) -> EscalationPolicy:
    return EscalationPolicy(
        id=orm.id, org_id=orm.org_id, name=orm.name,
        is_default=orm.is_default, trigger_after_hours=orm.trigger_after_hours,
        levels=list(orm.levels or []),
        created_at=orm.created_at, updated_at=orm.updated_at,
    )


def _escalation_to_entity(orm: EscalationORM) -> Escalation:
    return Escalation(
        id=orm.id, org_id=orm.org_id,
        action_item_id=orm.action_item_id, policy_id=orm.policy_id,
        current_level=orm.current_level, status=orm.status,
        history=list(orm.history or []),
        triggered_at=orm.triggered_at, resolved_at=orm.resolved_at,
        created_at=orm.created_at, updated_at=orm.updated_at,
    )


                                                                     

class SQLNotificationRepository(INotificationRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, n: Notification) -> Notification:
        orm = NotificationORM(
            id=n.id, org_id=n.org_id, recipient_id=n.recipient_id,
            event_type=n.event_type, channel=n.channel, status=n.status,
            subject=n.subject, body=n.body,
            related_item_id=n.related_item_id, related_item_type=n.related_item_type,
            payload=n.payload,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _notif_to_entity(orm)

    async def bulk_create(self, notifications: list[Notification]) -> list[Notification]:
        orm_objects = []
        for n in notifications:
            orm = NotificationORM(
                id=n.id, org_id=n.org_id, recipient_id=n.recipient_id,
                event_type=n.event_type, channel=n.channel, status=n.status,
                subject=n.subject, body=n.body,
                related_item_id=n.related_item_id, related_item_type=n.related_item_type,
                payload=n.payload,
            )
            self._db.add(orm)
            orm_objects.append(orm)
        await self._db.flush()
        return [_notif_to_entity(o) for o in orm_objects]

    async def get_by_id(self, notif_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None:
        result = await self._db.execute(
            select(NotificationORM).where(
                NotificationORM.id == notif_id,
                NotificationORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _notif_to_entity(orm) if orm else None

    async def list_inbox(
        self, recipient_id: uuid.UUID, org_id: uuid.UUID,
        limit: int = 30, cursor_id: uuid.UUID | None = None,
        unread_only: bool = False,
    ) -> list[Notification]:
        q = select(NotificationORM).where(
            NotificationORM.recipient_id == recipient_id,
            NotificationORM.org_id == org_id,
            NotificationORM.channel == "in_app",
        )
        if unread_only:
            q = q.where(NotificationORM.read_at.is_(None))
        if cursor_id:
            q = q.where(NotificationORM.id < cursor_id)
        q = q.order_by(NotificationORM.created_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_notif_to_entity(r) for r in result.scalars().all()]

    async def count_unread(self, recipient_id: uuid.UUID, org_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self._db.execute(
            select(func.count(NotificationORM.id)).where(
                NotificationORM.recipient_id == recipient_id,
                NotificationORM.org_id == org_id,
                NotificationORM.channel == "in_app",
                NotificationORM.read_at.is_(None),
            )
        )
        return result.scalar_one() or 0

    async def mark_read(self, notif_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None:
        now = datetime.now(timezone.utc)
        await self._db.execute(
            update(NotificationORM)
            .where(NotificationORM.id == notif_id, NotificationORM.org_id == org_id)
            .values(read_at=now, status=NotifStatus.READ, updated_at=now)
        )
        return await self.get_by_id(notif_id, org_id)

    async def mark_all_read(self, recipient_id: uuid.UUID, org_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        result = await self._db.execute(
            update(NotificationORM)
            .where(
                NotificationORM.recipient_id == recipient_id,
                NotificationORM.org_id == org_id,
                NotificationORM.read_at.is_(None),
                NotificationORM.channel == "in_app",
            )
            .values(read_at=now, status=NotifStatus.READ, updated_at=now)
        )
        return result.rowcount                              

    async def update(self, n: Notification) -> Notification:
        result = await self._db.execute(
            select(NotificationORM).where(NotificationORM.id == n.id)
        )
        orm = result.scalar_one()
        orm.status = n.status
        orm.sent_at = n.sent_at
        orm.read_at = n.read_at
        orm.failed_reason = n.failed_reason
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return _notif_to_entity(orm)


                                                                    

class SQLEscalationPolicyRepository(IEscalationPolicyRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, policy: EscalationPolicy) -> EscalationPolicy:
        orm = EscalationPolicyORM(
            id=policy.id, org_id=policy.org_id, name=policy.name,
            is_default=policy.is_default,
            trigger_after_hours=policy.trigger_after_hours,
            levels=policy.levels,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _policy_to_entity(orm)

    async def get_by_id(self, policy_id: uuid.UUID, org_id: uuid.UUID) -> EscalationPolicy | None:
        result = await self._db.execute(
            select(EscalationPolicyORM).where(
                EscalationPolicyORM.id == policy_id,
                EscalationPolicyORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _policy_to_entity(orm) if orm else None

    async def get_default(self, org_id: uuid.UUID) -> EscalationPolicy | None:
        result = await self._db.execute(
            select(EscalationPolicyORM).where(
                EscalationPolicyORM.org_id == org_id,
                EscalationPolicyORM.is_default.is_(True),
            ).limit(1)
        )
        orm = result.scalar_one_or_none()
        return _policy_to_entity(orm) if orm else None

    async def list_by_org(self, org_id: uuid.UUID) -> list[EscalationPolicy]:
        result = await self._db.execute(
            select(EscalationPolicyORM).where(EscalationPolicyORM.org_id == org_id)
            .order_by(EscalationPolicyORM.is_default.desc())
        )
        return [_policy_to_entity(r) for r in result.scalars().all()]

    async def update(self, policy: EscalationPolicy) -> EscalationPolicy:
        result = await self._db.execute(
            select(EscalationPolicyORM).where(EscalationPolicyORM.id == policy.id)
        )
        orm = result.scalar_one()
        orm.name = policy.name
        orm.is_default = policy.is_default
        orm.trigger_after_hours = policy.trigger_after_hours
        orm.levels = policy.levels
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return _policy_to_entity(orm)

    async def ensure_default_exists(self, org_id: uuid.UUID) -> EscalationPolicy:
        existing = await self.get_default(org_id)
        if existing:
            return existing
        default = EscalationPolicy(
            id=uuid.uuid4(), org_id=org_id, name="Default Escalation Policy",
            is_default=True, trigger_after_hours=24,
            levels=[
                {"level": 1, "notify": "owner",      "after_hours": 0},
                {"level": 2, "notify": "admin",      "after_hours": 24},
                {"level": 3, "notify": "owner_role", "after_hours": 48},
            ],
        )
        return await self.create(default)


                                                                     

class SQLEscalationRepository(IEscalationRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, esc: Escalation) -> Escalation:
        orm = EscalationORM(
            id=esc.id, org_id=esc.org_id,
            action_item_id=esc.action_item_id, policy_id=esc.policy_id,
            current_level=esc.current_level, status=esc.status,
            history=esc.history, triggered_at=esc.triggered_at,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _escalation_to_entity(orm)

    async def get_by_id(self, esc_id: uuid.UUID, org_id: uuid.UUID) -> Escalation | None:
        result = await self._db.execute(
            select(EscalationORM).where(
                EscalationORM.id == esc_id,
                EscalationORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _escalation_to_entity(orm) if orm else None

    async def get_by_action_item(self, action_item_id: uuid.UUID, org_id: uuid.UUID) -> Escalation | None:
        result = await self._db.execute(
            select(EscalationORM).where(
                EscalationORM.action_item_id == action_item_id,
                EscalationORM.org_id == org_id,
                EscalationORM.status == EscalationStatus.ACTIVE,
            ).limit(1)
        )
        orm = result.scalar_one_or_none()
        return _escalation_to_entity(orm) if orm else None

    async def list_active(
        self, org_id: uuid.UUID, limit: int = 50, cursor_id: uuid.UUID | None = None
    ) -> list[Escalation]:
        return await self.list_all(org_id, status=EscalationStatus.ACTIVE,
                                   limit=limit, cursor_id=cursor_id)

    async def list_all(
        self, org_id: uuid.UUID, status: str | None = None,
        limit: int = 50, cursor_id: uuid.UUID | None = None,
    ) -> list[Escalation]:
        q = select(EscalationORM).where(EscalationORM.org_id == org_id)
        if status:
            q = q.where(EscalationORM.status == status)
        if cursor_id:
            q = q.where(EscalationORM.id < cursor_id)
        q = q.order_by(EscalationORM.created_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_escalation_to_entity(r) for r in result.scalars().all()]

    async def update(self, esc: Escalation) -> Escalation:
        result = await self._db.execute(
            select(EscalationORM).where(EscalationORM.id == esc.id)
        )
        orm = result.scalar_one()
        orm.current_level = esc.current_level
        orm.status = esc.status
        orm.history = esc.history
        orm.resolved_at = esc.resolved_at
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return _escalation_to_entity(orm)

    async def get_due_for_advancement(self, as_of: datetime) -> list[Escalation]:
           
        result = await self._db.execute(
            select(EscalationORM).where(EscalationORM.status == EscalationStatus.ACTIVE)
        )
        all_active = [_escalation_to_entity(r) for r in result.scalars().all()]

        due = []
        for esc in all_active:
            if esc.history:
                last_entry = esc.history[-1]
                last_at_str = last_entry.get("at", "")
                try:
                    import datetime as dt
                    last_at = dt.datetime.fromisoformat(last_at_str)
                    if last_at.tzinfo is None:
                        last_at = last_at.replace(tzinfo=timezone.utc)
                    hours_elapsed = (as_of - last_at).total_seconds() / 3600
                    if hours_elapsed >= 24:
                        due.append(esc)
                except (ValueError, TypeError):
                    pass
        return due
