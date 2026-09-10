   
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class GetMeetingQuery:
    meeting_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetProcessingStatusQuery:
    meeting_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListMeetingsQuery:
    org_id: uuid.UUID
    limit: int = 50
    cursor_id: uuid.UUID | None = None
                                                      
                                             
    created_by: uuid.UUID | None = None
    status_filter: str | None = None
