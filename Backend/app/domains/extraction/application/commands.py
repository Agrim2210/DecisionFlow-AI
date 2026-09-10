   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RunPipelineCommand:
    meeting_id: uuid.UUID
    org_id: uuid.UUID
                         
                              
                                          


@dataclass(frozen=True)
class UpdateDecisionCommand:
    decision_id: uuid.UUID
    org_id: uuid.UUID
    updated_by: uuid.UUID
    status: str | None = None
    title: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class UpdateTaskStatusCommand:
    task_id: uuid.UUID
    org_id: uuid.UUID
    updated_by: uuid.UUID
    new_status: str
    note: str | None = None


@dataclass(frozen=True)
class AssignTaskCommand:
    task_id: uuid.UUID
    org_id: uuid.UUID
    assigned_by: uuid.UUID
    owner_id: uuid.UUID


@dataclass(frozen=True)
class UpdateTaskCommand:
    task_id: uuid.UUID
    org_id: uuid.UUID
    updated_by: uuid.UUID
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    due_date: datetime | None = None
    owner_id: uuid.UUID | None = None


@dataclass(frozen=True)
class UpdateRiskStatusCommand:
    risk_id: uuid.UUID
    org_id: uuid.UUID
    updated_by: uuid.UUID
    new_status: str                                          


@dataclass(frozen=True)
class AnswerQuestionCommand:
    question_id: uuid.UUID
    org_id: uuid.UUID
    answered_by: uuid.UUID
    answer: str
