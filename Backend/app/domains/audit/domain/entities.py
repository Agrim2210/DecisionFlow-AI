from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ActorType:
    USER   = "user"
    SYSTEM = "system"
    AI     = "ai"
    ALL    = frozenset({"user", "system", "ai"})


class AggregateType:
    DECISION    = "decision"
    ACTION_ITEM = "action_item"
    MEETING     = "meeting"
    RISK        = "risk"
    ESCALATION  = "escalation"
    USER        = "user"
    ORGANIZATION= "organization"
    POLICY      = "policy"


@dataclass(frozen=True)
class AuditLog:
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
    occurred_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_user_action(self) -> bool:
        return self.actor_type == ActorType.USER

    @property
    def is_system_action(self) -> bool:
        return self.actor_type == ActorType.SYSTEM

    @property
    def is_create(self) -> bool:
        return not self.before_state and bool(self.after_state)

    @property
    def is_delete(self) -> bool:
        return bool(self.before_state) and not self.after_state

    @property
    def is_update(self) -> bool:
        return bool(self.before_state) and bool(self.after_state)
