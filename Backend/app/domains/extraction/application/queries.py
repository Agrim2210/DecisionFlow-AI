   
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class ListDecisionsQuery:
    org_id: uuid.UUID
    limit: int = 50
    cursor_id: uuid.UUID | None = None
    decision_type: str | None = None
    status: str | None = None
    meeting_id: uuid.UUID | None = None


@dataclass(frozen=True)
class GetDecisionQuery:
    decision_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListTasksQuery:
    org_id: uuid.UUID
    limit: int = 50
    cursor_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None                                             
    status: str | None = None
    meeting_id: uuid.UUID | None = None
    overdue_only: bool = False


@dataclass(frozen=True)
class GetTaskQuery:
    task_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListRisksQuery:
    org_id: uuid.UUID
    meeting_id: uuid.UUID | None = None
    severity: str | None = None
    status: str | None = None
    limit: int = 50


@dataclass(frozen=True)
class GetRiskQuery:
    risk_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListQuestionsQuery:
    org_id: uuid.UUID
    meeting_id: uuid.UUID | None = None
    status: str | None = None


@dataclass(frozen=True)
class GetMeetingExtractionQuery:
                                                      
    meeting_id: uuid.UUID
    org_id: uuid.UUID
