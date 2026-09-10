   
from __future__ import annotations

from dataclasses import dataclass

from app.domains.graph.domain.exceptions import (
    InvalidDependencyTypeError,
)


                                                                     

_VALID_DEPENDENCY_TYPES = frozenset({
    "finish_to_start",
    "start_to_start",
    "finish_to_finish",
})

_VALID_DETECTED_BY = frozenset({"ai", "manual"})


                                                                     

@dataclass(frozen=True)
class DependencyType:
       
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_DEPENDENCY_TYPES:
            raise InvalidDependencyTypeError(
                f"'{self.value}' is not a valid dependency type. "
                f"Valid: {sorted(_VALID_DEPENDENCY_TYPES)}"
            )

    @property
    def is_finish_to_start(self) -> bool:
        return self.value == "finish_to_start"

    @property
    def is_start_to_start(self) -> bool:
        return self.value == "start_to_start"

    @property
    def is_finish_to_finish(self) -> bool:
        return self.value == "finish_to_finish"

    @property
    def label(self) -> str:
                                               
        return {
            "finish_to_start":  "Finish → Start",
            "start_to_start":   "Start → Start",
            "finish_to_finish": "Finish → Finish",
        }.get(self.value, self.value)

    def __str__(self) -> str:
        return self.value

                                                                     
    FINISH_TO_START  = "finish_to_start"
    START_TO_START   = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    ALL = _VALID_DEPENDENCY_TYPES

    @classmethod
    def safe(cls, value: str) -> "DependencyType":
                                                              
        return cls(value if value in _VALID_DEPENDENCY_TYPES else "finish_to_start")


                                                                    

@dataclass(frozen=True)
class DetectedBy:
       
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_DETECTED_BY:
            raise ValueError(
                f"'{self.value}' is not a valid detected_by value. "
                f"Valid: {sorted(_VALID_DETECTED_BY)}"
            )

    @property
    def is_ai(self) -> bool:
        return self.value == "ai"

    @property
    def is_manual(self) -> bool:
        return self.value == "manual"

    def __str__(self) -> str:
        return self.value

                                                                     
    AI     = "ai"
    MANUAL = "manual"

    @classmethod
    def safe(cls, value: str) -> "DetectedBy":
        return cls(value if value in _VALID_DETECTED_BY else "manual")


                                                                    

@dataclass(frozen=True)
class ConfidenceScore:
       
    value: float

    def __post_init__(self) -> None:
        clamped = max(0.0, min(1.0, float(self.value)))
        object.__setattr__(self, "value", round(clamped, 2))

    @property
    def is_high(self) -> bool:
                                                    
        return self.value >= 0.85

    @property
    def is_low(self) -> bool:
                                                     
        return self.value < 0.65

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def safe(cls, value: float | None) -> "ConfidenceScore":
        return cls(value if value is not None else 1.0)


                                                                    

@dataclass(frozen=True)
class GraphEdge:
       
    id: str
    source: str                                            
    target: str                                              
    dependency_type: str
    detected_by: str
    confidence_score: float
    label: str = ""                                     

    @property
    def is_ai_detected(self) -> bool:
        return self.detected_by == "ai"


                                                                    

@dataclass(frozen=True)
class GraphNode:
       
    id: str                                       
    label: str                                                   
    status: str                                   
    priority: str                           
    owner_id: str | None                                    
    is_overdue: bool = False
    is_unassigned: bool = False
    meeting_id: str = ""

    @classmethod
    def from_task(cls, task) -> "GraphNode":
                                                                
        return cls(
            id=str(task.id),
            label=task.title[:60],
            status=task.status,
            priority=task.priority,
            owner_id=str(task.owner_id) if task.owner_id else None,
            is_overdue=task.is_overdue,
            is_unassigned=task.is_unassigned,
            meeting_id=str(task.meeting_id),
        )
