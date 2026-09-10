   
from __future__ import annotations

from dataclasses import dataclass

from app.domains.extraction.domain.exceptions import (
    AIExtractionError,
    InvalidTaskTransitionError,
)


                                                                     

_VALID_DECISION_TYPES = frozenset({"strategic", "operational", "technical", "financial"})
_VALID_DECISION_STATUSES = frozenset({"active", "superseded", "cancelled"})


@dataclass(frozen=True)
class DecisionType:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_DECISION_TYPES:
            raise AIExtractionError(
                f"Invalid decision type '{self.value}'. "
                f"Valid: {sorted(_VALID_DECISION_TYPES)}"
            )

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "DecisionType":
                                                          
        return cls(value if value in _VALID_DECISION_TYPES else "operational")


@dataclass(frozen=True)
class DecisionStatus:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_DECISION_STATUSES:
            raise AIExtractionError(
                f"Invalid decision status '{self.value}'. "
                f"Valid: {sorted(_VALID_DECISION_STATUSES)}"
            )

    def __str__(self) -> str:
        return self.value


                                                                     

_VALID_TASK_STATUSES = frozenset({
    "pending", "in_progress", "completed", "blocked", "cancelled", "overdue"
})
_VALID_PRIORITIES = frozenset({"critical", "high", "medium", "low"})

                                                
_TASK_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending":     frozenset({"in_progress", "cancelled", "blocked", "overdue"}),
    "in_progress": frozenset({"completed", "blocked", "cancelled", "overdue"}),
    "blocked":     frozenset({"in_progress", "cancelled"}),
    "overdue":     frozenset({"in_progress", "completed", "cancelled"}),
    "completed":   frozenset(),             
    "cancelled":   frozenset(),             
}


@dataclass(frozen=True)
class TaskStatus:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_TASK_STATUSES:
            raise InvalidTaskTransitionError(
                f"Invalid task status '{self.value}'. "
                f"Valid: {sorted(_VALID_TASK_STATUSES)}"
            )

    def can_transition_to(self, next_status: str) -> bool:
        return next_status in _TASK_TRANSITIONS.get(self.value, frozenset())

    def assert_can_transition_to(self, next_status: str) -> None:
        if not self.can_transition_to(next_status):
            raise InvalidTaskTransitionError(
                f"Cannot move task from '{self.value}' → '{next_status}'. "
                f"Allowed: {sorted(_TASK_TRANSITIONS.get(self.value, set()))}"
            )

    @property
    def is_terminal(self) -> bool:
        return self.value in ("completed", "cancelled")

    @property
    def is_active(self) -> bool:
        return self.value in ("pending", "in_progress", "blocked", "overdue")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "TaskStatus":
        return cls(value if value in _VALID_TASK_STATUSES else "pending")


@dataclass(frozen=True)
class TaskPriority:
    value: str

                                                    
    _LEVELS: dict[str, int] = None                            

    def __post_init__(self) -> None:
        if self.value not in _VALID_PRIORITIES:
            raise AIExtractionError(
                f"Invalid priority '{self.value}'. "
                f"Valid: {sorted(_VALID_PRIORITIES)}"
            )

    @property
    def level(self) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(self.value, 2)

    def is_higher_than(self, other: "TaskPriority") -> bool:
        return self.level > other.level

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "TaskPriority":
        return cls(value if value in _VALID_PRIORITIES else "medium")


                                                                     

_VALID_RISK_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
_VALID_RISK_TYPES = frozenset({
    "unclear_ownership", "deadline_conflict", "missing_dependency",
    "unrealistic_timeline", "circular_dependency", "no_follow_up",
})
_VALID_RISK_STATUSES = frozenset({"open", "acknowledged", "resolved", "dismissed"})

_SEVERITY_LEVELS = {"critical": 4, "high": 3, "medium": 2, "low": 1}


@dataclass(frozen=True)
class RiskSeverity:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_RISK_SEVERITIES:
            raise AIExtractionError(
                f"Invalid risk severity '{self.value}'. "
                f"Valid: {sorted(_VALID_RISK_SEVERITIES)}"
            )

    @property
    def level(self) -> int:
        return _SEVERITY_LEVELS.get(self.value, 1)

    def is_at_least(self, minimum: str) -> bool:
        return self.level >= _SEVERITY_LEVELS.get(minimum, 1)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "RiskSeverity":
        return cls(value if value in _VALID_RISK_SEVERITIES else "medium")


@dataclass(frozen=True)
class RiskType:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_RISK_TYPES:
                                                                               
            object.__setattr__(self, "value", "no_follow_up")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "RiskType":
        return cls(value if value in _VALID_RISK_TYPES else "no_follow_up")


                                                                     

@dataclass(frozen=True)
class ConfidenceScore:
                                                                
    value: float

    def __post_init__(self) -> None:
        clamped = max(0.0, min(1.0, float(self.value)))
        object.__setattr__(self, "value", round(clamped, 2))

    @property
    def is_low(self) -> bool:
        return self.value < 0.7

    @property
    def is_high(self) -> bool:
        return self.value >= 0.85

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def safe(cls, value: float | None) -> "ConfidenceScore":
        return cls(value if value is not None else 1.0)
