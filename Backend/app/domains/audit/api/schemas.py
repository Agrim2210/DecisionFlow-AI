from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    actor_id: uuid.UUID
    actor_type: str
    event_type: str
    aggregate_type: str
    aggregate_id: uuid.UUID
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    ip_address: str | None
    metadata: dict[str, Any]
    occurred_at: str


class AuditListResponse(BaseModel):
    logs: list[AuditLogResponse]
    has_next: bool
    next_cursor: str | None
    total: int | None = None


def map_audit_log(log: Any) -> AuditLogResponse:
    return AuditLogResponse(
        id=log.id,
        org_id=log.org_id,
        actor_id=log.actor_id,
        actor_type=log.actor_type,
        event_type=log.event_type,
        aggregate_type=log.aggregate_type,
        aggregate_id=log.aggregate_id,
        before_state=log.before_state or {},
        after_state=log.after_state or {},
        ip_address=log.ip_address,
        metadata=log.metadata or {},
        occurred_at=log.occurred_at.isoformat(),
    )
