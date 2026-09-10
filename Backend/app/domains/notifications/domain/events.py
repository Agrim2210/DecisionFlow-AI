   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class NotificationSent:
    event_id: uuid.UUID
    org_id: uuid.UUID
    notification_id: uuid.UUID
    recipient_id: uuid.UUID
    channel: str
    event_type: str
    occurred_at: datetime

    @classmethod
    def create(cls, org_id, notification_id, recipient_id, channel, event_type) -> "NotificationSent":
        return cls(event_id=uuid.uuid4(), org_id=org_id, notification_id=notification_id,
                   recipient_id=recipient_id, channel=channel, event_type=event_type,
                   occurred_at=_now())


@dataclass(frozen=True)
class EscalationTriggered:
    event_id: uuid.UUID
    org_id: uuid.UUID
    escalation_id: uuid.UUID
    action_item_id: uuid.UUID
    level: int
    occurred_at: datetime

    @classmethod
    def create(cls, org_id, escalation_id, action_item_id, level) -> "EscalationTriggered":
        return cls(event_id=uuid.uuid4(), org_id=org_id, escalation_id=escalation_id,
                   action_item_id=action_item_id, level=level, occurred_at=_now())


@dataclass(frozen=True)
class EscalationResolved:
    event_id: uuid.UUID
    org_id: uuid.UUID
    escalation_id: uuid.UUID
    action_item_id: uuid.UUID
    resolved_by: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(cls, org_id, escalation_id, action_item_id, resolved_by) -> "EscalationResolved":
        return cls(event_id=uuid.uuid4(), org_id=org_id, escalation_id=escalation_id,
                   action_item_id=action_item_id, resolved_by=resolved_by, occurred_at=_now())
