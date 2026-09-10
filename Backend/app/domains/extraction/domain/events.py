   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PipelineStarted:
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(cls, org_id: uuid.UUID, meeting_id: uuid.UUID) -> "PipelineStarted":
        return cls(event_id=uuid.uuid4(), org_id=org_id,
                   meeting_id=meeting_id, occurred_at=_now())


@dataclass(frozen=True)
class PipelineCompleted:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    decisions_count: int
    tasks_count: int
    risks_count: int
    questions_count: int
    total_tokens_used: int
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        meeting_id: uuid.UUID,
        decisions_count: int,
        tasks_count: int,
        risks_count: int,
        questions_count: int,
        total_tokens_used: int = 0,
    ) -> "PipelineCompleted":
        return cls(
            event_id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
            decisions_count=decisions_count, tasks_count=tasks_count,
            risks_count=risks_count, questions_count=questions_count,
            total_tokens_used=total_tokens_used, occurred_at=_now(),
        )


@dataclass(frozen=True)
class PipelineFailed:
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    failed_at_stage: int
    error_message: str
    occurred_at: datetime

    @classmethod
    def create(cls, org_id: uuid.UUID, meeting_id: uuid.UUID,
               stage: int, error: str) -> "PipelineFailed":
        return cls(event_id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
                   failed_at_stage=stage, error_message=error, occurred_at=_now())


@dataclass(frozen=True)
class DecisionExtracted:
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    decision_id: uuid.UUID
    decision_type: str
    confidence_score: float
    occurred_at: datetime

    @classmethod
    def create(cls, org_id: uuid.UUID, meeting_id: uuid.UUID,
               decision_id: uuid.UUID, decision_type: str,
               confidence_score: float) -> "DecisionExtracted":
        return cls(event_id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
                   decision_id=decision_id, decision_type=decision_type,
                   confidence_score=confidence_score, occurred_at=_now())


@dataclass(frozen=True)
class TaskCreated:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    task_id: uuid.UUID
    owner_id: uuid.UUID | None
    due_date: datetime | None
    priority: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        meeting_id: uuid.UUID,
        task_id: uuid.UUID,
        owner_id: uuid.UUID | None,
        due_date: datetime | None,
        priority: str,
    ) -> "TaskCreated":
        return cls(event_id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
                   task_id=task_id, owner_id=owner_id, due_date=due_date,
                   priority=priority, occurred_at=_now())


@dataclass(frozen=True)
class TaskStatusChanged:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    task_id: uuid.UUID
    old_status: str
    new_status: str
    changed_by: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        old_status: str,
        new_status: str,
        changed_by: uuid.UUID,
    ) -> "TaskStatusChanged":
        return cls(event_id=uuid.uuid4(), org_id=org_id, task_id=task_id,
                   old_status=old_status, new_status=new_status,
                   changed_by=changed_by, occurred_at=_now())


@dataclass(frozen=True)
class RiskFlagged:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    risk_id: uuid.UUID
    risk_type: str
    severity: str
    related_item_id: uuid.UUID
    related_item_type: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        meeting_id: uuid.UUID,
        risk_id: uuid.UUID,
        risk_type: str,
        severity: str,
        related_item_id: uuid.UUID,
        related_item_type: str,
    ) -> "RiskFlagged":
        return cls(event_id=uuid.uuid4(), org_id=org_id, meeting_id=meeting_id,
                   risk_id=risk_id, risk_type=risk_type, severity=severity,
                   related_item_id=related_item_id, related_item_type=related_item_type,
                   occurred_at=_now())


@dataclass(frozen=True)
class TaskAssigned:
    event_id: uuid.UUID
    org_id: uuid.UUID
    task_id: uuid.UUID
    new_owner_id: uuid.UUID
    assigned_by: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(cls, org_id: uuid.UUID, task_id: uuid.UUID,
               new_owner_id: uuid.UUID, assigned_by: uuid.UUID) -> "TaskAssigned":
        return cls(event_id=uuid.uuid4(), org_id=org_id, task_id=task_id,
                   new_owner_id=new_owner_id, assigned_by=assigned_by, occurred_at=_now())
