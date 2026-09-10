   
from __future__ import annotations

from dataclasses import dataclass

from app.domains.notifications.domain.exceptions import (
    InvalidChannelError,
    NotificationDeliveryError,
)


                                                                     

_VALID_CHANNELS = frozenset({"in_app", "email", "slack"})
_VALID_NOTIF_STATUSES = frozenset({"pending", "sent", "delivered", "failed", "read"})
_VALID_ESCALATION_STATUSES = frozenset({"active", "resolved", "dismissed"})
_VALID_ESCALATION_LEVELS = frozenset({1, 2, 3, 4, 5})
_VALID_NOTIFY_TYPES = frozenset({"owner", "admin", "owner_role"})

_VALID_EVENT_TYPES = frozenset({
    "task_assigned",
    "task_overdue",
    "task_completed",
    "task_blocked",
    "escalation_triggered",
    "escalation_level_2",
    "escalation_level_3",
    "escalation_resolved",
    "meeting_processed",
    "pipeline_failed",
    "risk_detected",
    "risk_critical",
    "user_invited",
    "role_changed",
})


                                                                     

@dataclass(frozen=True)
class NotifChannel:
       
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_CHANNELS:
            raise InvalidChannelError(
                f"'{self.value}' is not a valid notification channel. "
                f"Valid: {sorted(_VALID_CHANNELS)}"
            )

    @property
    def is_in_app(self) -> bool:
        return self.value == "in_app"

    @property
    def is_email(self) -> bool:
        return self.value == "email"

    @property
    def is_slack(self) -> bool:
        return self.value == "slack"

    def __str__(self) -> str:
        return self.value

                                                                     
    IN_APP = "in_app"
    EMAIL  = "email"
    SLACK  = "slack"
    ALL    = _VALID_CHANNELS

    @classmethod
    def safe(cls, value: str) -> "NotifChannel":
        return cls(value if value in _VALID_CHANNELS else "in_app")


                                                                     

                                                  
_NOTIF_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending":   frozenset({"sent", "failed"}),
    "sent":      frozenset({"delivered", "read", "failed"}),
    "delivered": frozenset({"read"}),
    "failed":    frozenset({"pending"}),                    
    "read":      frozenset(),                            
}


@dataclass(frozen=True)
class NotifStatus:
                                                              
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_NOTIF_STATUSES:
            raise NotificationDeliveryError(
                f"'{self.value}' is not a valid notification status. "
                f"Valid: {sorted(_VALID_NOTIF_STATUSES)}"
            )

    def can_transition_to(self, next_status: str) -> bool:
        return next_status in _NOTIF_STATUS_TRANSITIONS.get(self.value, frozenset())

    @property
    def is_terminal(self) -> bool:
        return self.value == "read"

    @property
    def is_delivered(self) -> bool:
        return self.value in ("sent", "delivered", "read")

    @property
    def is_failed(self) -> bool:
        return self.value == "failed"

    def __str__(self) -> str:
        return self.value

                                                                     
    PENDING   = "pending"
    SENT      = "sent"
    DELIVERED = "delivered"
    FAILED    = "failed"
    READ      = "read"

    @classmethod
    def safe(cls, value: str) -> "NotifStatus":
        return cls(value if value in _VALID_NOTIF_STATUSES else "pending")


                                                                     

@dataclass(frozen=True)
class EscalationLevel:
       
    value: int

    def __post_init__(self) -> None:
        if self.value not in _VALID_ESCALATION_LEVELS:
            raise ValueError(
                f"Escalation level must be 1–5, got {self.value}"
            )

    @property
    def is_first(self) -> bool:
        return self.value == 1

    @property
    def is_final(self) -> bool:
        return self.value >= 3

    def next(self) -> "EscalationLevel":
                                               
        if self.value >= max(_VALID_ESCALATION_LEVELS):
            raise ValueError("Already at maximum escalation level")
        return EscalationLevel(self.value + 1)

    def __str__(self) -> str:
        return str(self.value)

    def __lt__(self, other: "EscalationLevel") -> bool:
        return self.value < other.value

    def __le__(self, other: "EscalationLevel") -> bool:
        return self.value <= other.value

                                                                     
    ONE   = 1
    TWO   = 2
    THREE = 3


                                                                     

_ESC_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "active":    frozenset({"resolved", "dismissed"}),
    "resolved":  frozenset(),              
    "dismissed": frozenset(),              
}


@dataclass(frozen=True)
class EscalationStatus:
                                            
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_ESCALATION_STATUSES:
            raise ValueError(
                f"'{self.value}' is not a valid escalation status. "
                f"Valid: {sorted(_VALID_ESCALATION_STATUSES)}"
            )

    def can_transition_to(self, next_status: str) -> bool:
        return next_status in _ESC_STATUS_TRANSITIONS.get(self.value, frozenset())

    @property
    def is_active(self) -> bool:
        return self.value == "active"

    @property
    def is_terminal(self) -> bool:
        return self.value in ("resolved", "dismissed")

    def __str__(self) -> str:
        return self.value

                                                                     
    ACTIVE    = "active"
    RESOLVED  = "resolved"
    DISMISSED = "dismissed"


                                                                     

@dataclass(frozen=True)
class PolicyConfig:
       
    level: int
    notify: str                                            
    after_hours: int                                                  

    def __post_init__(self) -> None:
        if self.level not in _VALID_ESCALATION_LEVELS:
            raise ValueError(f"Level must be 1–5, got {self.level}")
        if self.notify not in _VALID_NOTIFY_TYPES:
            raise ValueError(
                f"notify must be one of {sorted(_VALID_NOTIFY_TYPES)}, got '{self.notify}'"
            )
        if self.after_hours < 0 or self.after_hours > 720:               
            raise ValueError(f"after_hours must be 0–720, got {self.after_hours}")

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "notify": self.notify,
            "after_hours": self.after_hours,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PolicyConfig":
        return cls(
            level=int(data["level"]),
            notify=str(data["notify"]),
            after_hours=int(data.get("after_hours", 0)),
        )

    @classmethod
    def default_levels(cls) -> list["PolicyConfig"]:
                                                            
        return [
            cls(level=1, notify="owner",      after_hours=0),
            cls(level=2, notify="admin",      after_hours=24),
            cls(level=3, notify="owner_role", after_hours=48),
        ]
