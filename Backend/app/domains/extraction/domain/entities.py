   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


                                                                     

class DecisionType:
    STRATEGIC   = "strategic"
    OPERATIONAL = "operational"
    TECHNICAL   = "technical"
    FINANCIAL   = "financial"
    ALL = {STRATEGIC, OPERATIONAL, TECHNICAL, FINANCIAL}


class DecisionStatus:
    ACTIVE      = "active"
    SUPERSEDED  = "superseded"
    CANCELLED   = "cancelled"
    ALL = {ACTIVE, SUPERSEDED, CANCELLED}


class TaskStatus:
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    BLOCKED     = "blocked"
    CANCELLED   = "cancelled"
    OVERDUE     = "overdue"
    ALL = {PENDING, IN_PROGRESS, COMPLETED, BLOCKED, CANCELLED, OVERDUE}

                                                      
    TRANSITIONS: dict[str, list[str]] = {
        PENDING:     [IN_PROGRESS, CANCELLED, BLOCKED, OVERDUE],
        IN_PROGRESS: [COMPLETED, BLOCKED, CANCELLED, OVERDUE],
        BLOCKED:     [IN_PROGRESS, CANCELLED],
        OVERDUE:     [IN_PROGRESS, COMPLETED, CANCELLED],
        COMPLETED:   [],             
        CANCELLED:   [],             
    }

    @classmethod
    def can_transition(cls, current: str, nxt: str) -> bool:
        return nxt in cls.TRANSITIONS.get(current, [])


class TaskPriority:
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"
    ALL = {CRITICAL, HIGH, MEDIUM, LOW}


class RiskSeverity:
    CRITICAL = "critical"
    HIGH     = "high"
    MEDIUM   = "medium"
    LOW      = "low"


class RiskType:
    UNCLEAR_OWNERSHIP    = "unclear_ownership"
    DEADLINE_CONFLICT    = "deadline_conflict"
    MISSING_DEPENDENCY   = "missing_dependency"
    UNREALISTIC_TIMELINE = "unrealistic_timeline"
    CIRCULAR_DEPENDENCY  = "circular_dependency"
    NO_FOLLOW_UP         = "no_follow_up"


class RiskStatus:
    OPEN         = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED     = "resolved"
    DISMISSED    = "dismissed"


class QuestionStatus:
    OPEN     = "open"
    ANSWERED = "answered"
    DEFERRED = "deferred"


                                                                     

@dataclass
class Decision:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    title: str
    description: str
    decision_type: str                                             
    status: str = DecisionStatus.ACTIVE                              
    confidence_score: float = 1.0                                  
    ai_raw_output: dict = field(default_factory=dict)                         
    made_by: list[uuid.UUID] = field(default_factory=list)
    effective_date: datetime | None = None
    review_date: datetime | None = None
    embedding: list[float] | None = None                                                                                
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    deleted_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.status == DecisionStatus.ACTIVE

    @property
    def is_low_confidence(self) -> bool:
        return self.confidence_score < 0.7

    def supersede(self) -> None:
        self.status = DecisionStatus.SUPERSEDED
        self.updated_at = _now()


@dataclass
class ActionItem:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    decision_id: uuid.UUID | None                                           
    title: str
    description: str
    owner_id: uuid.UUID | None                                                        
    owner_name: str | None = None                                                     
    status: str = TaskStatus.PENDING
    priority: str = TaskPriority.MEDIUM
    due_date: datetime | None = None
    completed_at: datetime | None = None
    confidence_score: float = 1.0
    ai_raw_output: dict = field(default_factory=dict)
    embedding: list[float] | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    deleted_at: datetime | None = None

    @property
    def is_unassigned(self) -> bool:
        return self.owner_id is None

    @property
    def is_overdue(self) -> bool:
        if self.due_date is None or self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return False
        return self.due_date < _now()

    @property
    def is_terminal(self) -> bool:
        return self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)

    def transition(self, new_status: str) -> None:
        from app.domains.extraction.domain.exceptions import InvalidTaskTransitionError
        if not TaskStatus.can_transition(self.status, new_status):
            raise InvalidTaskTransitionError(
                f"Cannot move task from '{self.status}' → '{new_status}'"
            )
        self.status = new_status
        self.updated_at = _now()
        if new_status == TaskStatus.COMPLETED:
            self.completed_at = _now()

    def mark_overdue(self) -> None:
                                                
        if self.is_overdue and self.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
            self.status = TaskStatus.OVERDUE
            self.updated_at = _now()


@dataclass
class Risk:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    related_item_id: uuid.UUID                                             
    related_item_type: str                                              
    risk_type: str                                             
    severity: str                                                  
    description: str
    recommendation: str = ""
    status: str = RiskStatus.OPEN
    resolved_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def acknowledge(self) -> None:
        self.status = RiskStatus.ACKNOWLEDGED
        self.updated_at = _now()

    def resolve(self) -> None:
        self.status = RiskStatus.RESOLVED
        self.resolved_at = _now()
        self.updated_at = _now()

    def dismiss(self) -> None:
        self.status = RiskStatus.DISMISSED
        self.updated_at = _now()


@dataclass
class OpenQuestion:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    question: str
    context: str = ""                                                     
    status: str = QuestionStatus.OPEN
    answer: str | None = None
    answered_by: uuid.UUID | None = None
    answered_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def answer_question(self, answer: str, answered_by: uuid.UUID) -> None:
        self.answer = answer
        self.answered_by = answered_by
        self.answered_at = _now()
        self.status = QuestionStatus.ANSWERED
        self.updated_at = _now()


@dataclass
class MemoryChunk:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    source_type: str                                                                   
    source_id: uuid.UUID
    content: str                                                        
    embedding: list[float]                                                                          
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)


@dataclass
class PipelineResult:
       
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    decisions: list[Decision] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    open_questions: list[OpenQuestion] = field(default_factory=list)
    dependency_edges: list[dict] = field(default_factory=list)
                                                                                       
    memory_chunks: list[MemoryChunk] = field(default_factory=list)
    stage_timings: dict[str, float] = field(default_factory=dict)
    total_tokens_used: int = 0
    completed_at: datetime = field(default_factory=_now)
