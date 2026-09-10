   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class UploadMeetingCommand:
    org_id: uuid.UUID
    uploaded_by: uuid.UUID
    filename: str
    file_content: bytes
    content_type: str
    title: str | None = None
    meeting_date: datetime | None = None
    source: str = "upload"


@dataclass(frozen=True)
class PasteMeetingCommand:
    org_id: uuid.UUID
    pasted_by: uuid.UUID
    text: str
    title: str | None = None
    meeting_date: datetime | None = None
    source: str = "paste"


@dataclass(frozen=True)
class UpdateMeetingStatusCommand:
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    new_status: str
    current_stage: int | None = None
    stage_name: str | None = None
    error: str | None = None
    meta_updates: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DeleteMeetingCommand:
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    requested_by: uuid.UUID
