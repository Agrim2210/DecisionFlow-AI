from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domains.audit.domain.entities import AuditLog


class IAuditRepository(ABC):
    @abstractmethod
    async def append(self, log: AuditLog) -> AuditLog: ...

    @abstractmethod
    async def get_by_id(self, log_id: uuid.UUID, org_id: uuid.UUID) -> AuditLog | None: ...

    @abstractmethod
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
    ) -> list[AuditLog]: ...
