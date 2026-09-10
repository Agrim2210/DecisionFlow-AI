from __future__ import annotations

from dataclasses import dataclass

_VALID_ACTOR_TYPES     = frozenset({"user", "system", "ai"})
_VALID_AGGREGATE_TYPES = frozenset({
    "decision", "action_item", "meeting", "risk",
    "escalation", "user", "organization", "policy",
})


@dataclass(frozen=True)
class ActorType:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_ACTOR_TYPES:
            raise ValueError(f"Invalid actor type '{self.value}'. Valid: {sorted(_VALID_ACTOR_TYPES)}")

    @property
    def is_user(self) -> bool:
        return self.value == "user"

    @property
    def is_system(self) -> bool:
        return self.value == "system"

    @property
    def is_ai(self) -> bool:
        return self.value == "ai"

    def __str__(self) -> str:
        return self.value

    USER   = "user"
    SYSTEM = "system"
    AI     = "ai"

    @classmethod
    def safe(cls, value: str) -> "ActorType":
        return cls(value if value in _VALID_ACTOR_TYPES else "system")


@dataclass(frozen=True)
class AggregateType:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_AGGREGATE_TYPES:
            raise ValueError(f"Invalid aggregate type '{self.value}'.")

    def __str__(self) -> str:
        return self.value

    DECISION     = "decision"
    ACTION_ITEM  = "action_item"
    MEETING      = "meeting"
    RISK         = "risk"
    ESCALATION   = "escalation"
    USER         = "user"
    ORGANIZATION = "organization"
    POLICY       = "policy"

    @classmethod
    def safe(cls, value: str) -> "AggregateType":
        return cls(value if value in _VALID_AGGREGATE_TYPES else "meeting")


@dataclass(frozen=True)
class EventType:
    value: str

    def __post_init__(self) -> None:
        if not self.value or "." not in self.value:
            raise ValueError(
                f"EventType must follow 'aggregate.action' format, got '{self.value}'"
            )

    @property
    def aggregate(self) -> str:
        return self.value.split(".")[0]

    @property
    def action(self) -> str:
        return self.value.split(".", 1)[1]

    def __str__(self) -> str:
        return self.value

    DECISION_UPDATED       = "decision.updated"
    DECISION_SUPERSEDED    = "decision.superseded"
    TASK_CREATED           = "action_item.created"
    TASK_STATUS_CHANGED    = "action_item.status_changed"
    TASK_ASSIGNED          = "action_item.assigned"
    MEETING_UPLOADED       = "meeting.uploaded"
    MEETING_DELETED        = "meeting.deleted"
    RISK_STATUS_CHANGED    = "risk.status_changed"
    ESCALATION_TRIGGERED   = "escalation.triggered"
    ESCALATION_RESOLVED    = "escalation.resolved"
    USER_INVITED           = "user.invited"
    USER_ROLE_CHANGED      = "user.role_changed"
    USER_DEACTIVATED       = "user.deactivated"
    ORG_SETTINGS_UPDATED   = "organization.settings_updated"
    POLICY_CREATED         = "policy.created"
    POLICY_UPDATED         = "policy.updated"
