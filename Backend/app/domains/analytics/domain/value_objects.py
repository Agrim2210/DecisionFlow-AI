   
from __future__ import annotations

from dataclasses import dataclass

from app.domains.analytics.domain.exceptions import (
    InsufficientDataError,
    InvalidScoreError,
)


                                                                     

@dataclass(frozen=True)
class ReliabilityScore:
       
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            raise InvalidScoreError(
                f"ReliabilityScore must be between 0.0 and 100.0, got {self.value}"
            )
                                   
        object.__setattr__(self, "value", round(float(self.value), 2))

    @property
    def is_at_risk(self) -> bool:
                                                
        return self.value < 70.0

    @property
    def is_top_performer(self) -> bool:
                                                                   
        return self.value >= 90.0

    @property
    def grade(self) -> str:
                                       
        if self.value >= 90:
            return "A"
        elif self.value >= 75:
            return "B"
        elif self.value >= 60:
            return "C"
        elif self.value >= 40:
            return "D"
        return "F"

    @property
    def label(self) -> str:
                                   
        if self.value >= 90:
            return "Excellent"
        elif self.value >= 75:
            return "Good"
        elif self.value >= 60:
            return "Fair"
        elif self.value >= 40:
            return "Poor"
        return "Critical"

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.1f}%"

    @classmethod
    def compute(cls, tasks_on_time: int, tasks_assigned: int) -> "ReliabilityScore":
           
        if tasks_assigned == 0:
            return cls(100.0)
        return cls(round((tasks_on_time / tasks_assigned) * 100, 2))

    @classmethod
    def safe(cls, value: float | None) -> "ReliabilityScore":
                                                     
        if value is None:
            return cls(100.0)
        return cls(max(0.0, min(100.0, float(value))))


                                                                    

@dataclass(frozen=True)
class ExecutionRate:
       
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 100.0):
            raise InvalidScoreError(
                f"ExecutionRate must be between 0.0 and 100.0, got {self.value}"
            )
        object.__setattr__(self, "value", round(float(self.value), 2))

    @property
    def is_healthy(self) -> bool:
                                                
        return self.value >= 80.0

    @property
    def is_concerning(self) -> bool:
                                                                   
        return self.value < 50.0

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.1f}%"

    @classmethod
    def compute(cls, completed: int, total: int) -> "ExecutionRate":
                                                                
        if total == 0:
            return cls(0.0)
        return cls(round((completed / total) * 100, 2))

    @classmethod
    def safe(cls, value: float | None) -> "ExecutionRate":
        if value is None:
            return cls(0.0)
        return cls(max(0.0, min(100.0, float(value))))


                                                                    

@dataclass(frozen=True)
class MeetingROI:
       
    meeting_id: str
    decisions_count: int
    tasks_count: int
    tasks_completed: int
    tasks_on_time: int
    risks_identified: int
    risks_resolved: int
    open_questions: int
    execution_rate: float                         
    roi_score: float                                              

    def __post_init__(self) -> None:
        if not (0.0 <= self.roi_score <= 100.0):
            raise InvalidScoreError(
                f"ROI score must be 0.0 – 100.0, got {self.roi_score}"
            )

    @property
    def has_value(self) -> bool:
                                                                  
        return self.decisions_count > 0 or self.tasks_completed > 0

    @property
    def risk_resolution_rate(self) -> float:
        if self.risks_identified == 0:
            return 100.0
        return round((self.risks_resolved / self.risks_identified) * 100, 2)

    @property
    def summary(self) -> str:
                                                
        if self.roi_score >= 80:
            return "High-value meeting — strong decisions and execution"
        elif self.roi_score >= 60:
            return "Good meeting — most tasks progressing"
        elif self.roi_score >= 40:
            return "Average meeting — execution needs improvement"
        return "Low-value meeting — few decisions executed"

    @classmethod
    def compute(
        cls,
        meeting_id: str,
        decisions_count: int,
        tasks_count: int,
        tasks_completed: int,
        tasks_on_time: int,
        risks_identified: int,
        risks_resolved: int,
        open_questions: int,
    ) -> "MeetingROI":
           
                                   
        exec_rate = (tasks_completed / tasks_count * 100) if tasks_count > 0 else 0.0
        exec_component = exec_rate * 0.40

                                  
        has_decisions = min(decisions_count * 15, 30.0)                                            
        decision_component = has_decisions

                              
        if risks_identified > 0:
            risk_rate = (risks_resolved / risks_identified) * 100
        else:
            risk_rate = 100.0                             
        risk_component = risk_rate * 0.20

                                 
                                                       
        if open_questions == 0:
            closure_component = 10.0
        else:
            closure_component = max(0.0, 10.0 - (open_questions * 2))

        roi_score = round(
            exec_component + decision_component + risk_component + closure_component,
            2,
        )
        roi_score = max(0.0, min(100.0, roi_score))

        execution_rate = round(exec_rate, 2)

        return cls(
            meeting_id=meeting_id,
            decisions_count=decisions_count,
            tasks_count=tasks_count,
            tasks_completed=tasks_completed,
            tasks_on_time=tasks_on_time,
            risks_identified=risks_identified,
            risks_resolved=risks_resolved,
            open_questions=open_questions,
            execution_rate=execution_rate,
            roi_score=roi_score,
        )
