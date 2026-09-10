   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


                                                                     

class NotifChannel:
    IN_APP = "in_app"
    EMAIL  = "email"
    SLACK  = "slack"
    ALL    = {IN_APP, EMAIL, SLACK}


class NotifStatus:
    PENDING   = "pending"
    SENT      = "sent"
    DELIVERED = "delivered"
    FAILED    = "failed"
    READ      = "read"


class NotifEventType:
    TASK_ASSIGNED         = "task_assigned"
    TASK_OVERDUE          = "task_overdue"
    TASK_COMPLETED        = "task_completed"
    TASK_BLOCKED          = "task_blocked"
    ESCALATION_TRIGGERED  = "escalation_triggered"
    ESCALATION_LEVEL_2    = "escalation_level_2"
    ESCALATION_LEVEL_3    = "escalation_level_3"
    ESCALATION_RESOLVED   = "escalation_resolved"
    MEETING_PROCESSED     = "meeting_processed"
    PIPELINE_FAILED       = "pipeline_failed"
    RISK_DETECTED         = "risk_detected"
    RISK_CRITICAL         = "risk_critical"
    USER_INVITED          = "user_invited"
    ROLE_CHANGED          = "role_changed"


class EscalationLevel:
    ONE   = 1
    TWO   = 2
    THREE = 3


class EscalationStatus:
    ACTIVE    = "active"
    RESOLVED  = "resolved"
    DISMISSED = "dismissed"


                                                                     

@dataclass
class Notification:
       
    id: uuid.UUID
    org_id: uuid.UUID
    recipient_id: uuid.UUID
    event_type: str
    channel: str
    status: str = NotifStatus.PENDING
    subject: str = ""
    body: str = ""
    related_item_id: uuid.UUID | None = None
    related_item_type: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    sent_at: datetime | None = None
    read_at: datetime | None = None
    failed_reason: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    @property
    def is_sent(self) -> bool:
        return self.status in (NotifStatus.SENT, NotifStatus.DELIVERED, NotifStatus.READ)

    def mark_sent(self) -> None:
        self.status = NotifStatus.SENT
        self.sent_at = _now()
        self.updated_at = _now()

    def mark_read(self) -> None:
        self.status = NotifStatus.READ
        self.read_at = _now()
        self.updated_at = _now()

    def mark_failed(self, reason: str) -> None:
        self.status = NotifStatus.FAILED
        self.failed_reason = reason
        self.updated_at = _now()


@dataclass
class EscalationPolicy:
                                                                              
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    is_default: bool = True
    trigger_after_hours: int = 24
    levels: list[dict[str, Any]] = field(default_factory=lambda: [
        {"level": 1, "notify": "owner",      "after_hours": 0},
        {"level": 2, "notify": "admin",      "after_hours": 24},
        {"level": 3, "notify": "owner_role", "after_hours": 48},
    ])
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def get_level_config(self, level: int) -> dict[str, Any] | None:
        return next((l for l in self.levels if l["level"] == level), None)

    @property
    def max_level(self) -> int:
        return max((l["level"] for l in self.levels), default=3)


@dataclass
class Escalation:
       
    id: uuid.UUID
    org_id: uuid.UUID
    action_item_id: uuid.UUID
    policy_id: uuid.UUID
    current_level: int = EscalationLevel.ONE
    status: str = EscalationStatus.ACTIVE
    history: list[dict[str, Any]] = field(default_factory=list)
    triggered_at: datetime = field(default_factory=_now)
    resolved_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def is_active(self) -> bool:
        return self.status == EscalationStatus.ACTIVE

    def advance(self, new_level: int, notified_ids: list[uuid.UUID]) -> None:
        self.current_level = new_level
        self.history.append({
            "level": new_level,
            "action": "advanced",
            "notified_user_ids": [str(uid) for uid in notified_ids],
            "at": _now().isoformat(),
        })
        self.updated_at = _now()

    def trigger(self, notified_ids: list[uuid.UUID]) -> None:
        self.history.append({
            "level": EscalationLevel.ONE,
            "action": "triggered",
            "notified_user_ids": [str(uid) for uid in notified_ids],
            "at": _now().isoformat(),
        })
        self.updated_at = _now()

    def resolve(self, resolved_by: uuid.UUID) -> None:
        self.status = EscalationStatus.RESOLVED
        self.resolved_at = _now()
        self.history.append({
            "action": "resolved",
            "resolved_by": str(resolved_by),
            "at": _now().isoformat(),
        })
        self.updated_at = _now()

    def dismiss(self, dismissed_by: uuid.UUID) -> None:
        self.status = EscalationStatus.DISMISSED
        self.history.append({
            "action": "dismissed",
            "dismissed_by": str(dismissed_by),
            "at": _now().isoformat(),
        })
        self.updated_at = _now()

    def hours_since_trigger(self) -> float:
        delta = _now() - self.triggered_at
        return delta.total_seconds() / 3600
