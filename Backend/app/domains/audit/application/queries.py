from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ListAuditLogsQuery:
    org_id: uuid.UUID
    limit: int = 20
    cursor_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    aggregate_type: str | None = None
    event_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
