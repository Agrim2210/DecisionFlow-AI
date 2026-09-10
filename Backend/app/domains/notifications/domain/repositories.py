   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domains.notifications.domain.entities import (
    Escalation,
    EscalationPolicy,
    Notification,
)


class INotificationRepository(ABC):

    @abstractmethod
    async def create(self, notification: Notification) -> Notification: ...

    @abstractmethod
    async def bulk_create(self, notifications: list[Notification]) -> list[Notification]: ...

    @abstractmethod
    async def get_by_id(self, notif_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None: ...

    @abstractmethod
    async def list_inbox(
        self,
        recipient_id: uuid.UUID,
        org_id: uuid.UUID,
        limit: int = 30,
        cursor_id: uuid.UUID | None = None,
        unread_only: bool = False,
    ) -> list[Notification]: ...

    @abstractmethod
    async def count_unread(self, recipient_id: uuid.UUID, org_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def mark_read(self, notif_id: uuid.UUID, org_id: uuid.UUID) -> Notification | None: ...

    @abstractmethod
    async def mark_all_read(self, recipient_id: uuid.UUID, org_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def update(self, notification: Notification) -> Notification: ...


class IEscalationRepository(ABC):

    @abstractmethod
    async def create(self, escalation: Escalation) -> Escalation: ...

    @abstractmethod
    async def get_by_id(self, esc_id: uuid.UUID, org_id: uuid.UUID) -> Escalation | None: ...

    @abstractmethod
    async def get_by_action_item(
        self, action_item_id: uuid.UUID, org_id: uuid.UUID
    ) -> Escalation | None: ...

    @abstractmethod
    async def list_active(
        self, org_id: uuid.UUID, limit: int = 50, cursor_id: uuid.UUID | None = None
    ) -> list[Escalation]: ...

    @abstractmethod
    async def list_all(
        self,
        org_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
    ) -> list[Escalation]: ...

    @abstractmethod
    async def update(self, escalation: Escalation) -> Escalation: ...

    @abstractmethod
    async def get_due_for_advancement(self, as_of: datetime) -> list[Escalation]: ...


class IEscalationPolicyRepository(ABC):

    @abstractmethod
    async def create(self, policy: EscalationPolicy) -> EscalationPolicy: ...

    @abstractmethod
    async def get_by_id(self, policy_id: uuid.UUID, org_id: uuid.UUID) -> EscalationPolicy | None: ...

    @abstractmethod
    async def get_default(self, org_id: uuid.UUID) -> EscalationPolicy | None: ...

    @abstractmethod
    async def list_by_org(self, org_id: uuid.UUID) -> list[EscalationPolicy]: ...

    @abstractmethod
    async def update(self, policy: EscalationPolicy) -> EscalationPolicy: ...

    @abstractmethod
    async def ensure_default_exists(self, org_id: uuid.UUID) -> EscalationPolicy: ...
