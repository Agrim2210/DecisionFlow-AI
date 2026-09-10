                                                      
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class GetInboxQuery:
    recipient_id: uuid.UUID
    org_id: uuid.UUID
    limit: int = 30
    cursor_id: uuid.UUID | None = None
    unread_only: bool = False


@dataclass(frozen=True)
class GetUnreadCountQuery:
    recipient_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListEscalationsQuery:
    org_id: uuid.UUID
    status: str | None = None
    limit: int = 50
    cursor_id: uuid.UUID | None = None


@dataclass(frozen=True)
class GetEscalationQuery:
    escalation_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListPoliciesQuery:
    org_id: uuid.UUID
