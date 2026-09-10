   
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class GetMeetingGraphQuery:
                                                                     
    meeting_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetTaskDependenciesQuery:
                                                                           
    task_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetDependencyQuery:
                                               
    dep_id: uuid.UUID
    org_id: uuid.UUID
