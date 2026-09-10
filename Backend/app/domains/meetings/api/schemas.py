   
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


                                             
                 
                                             

class PasteMeetingRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=500_000)
    title: str | None = Field(default=None, max_length=500)
    meeting_date: datetime | None = None
    source: str = Field(default="paste", pattern=r"^(paste|zoom|meet|teams|manual)$")

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class ListMeetingsRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = None
    status: str | None = Field(
        default=None,
        pattern=r"^(uploaded|queued|processing|completed|failed)$",
    )


                                             
                  
                                             

class ProcessingStatusResponse(BaseModel):
    meeting_id: str
    status: str
    current_stage: int | None
    current_stage_name: str | None
    total_stages: int
    progress_pct: int
    error: str | None


class TranscriptResponse(BaseModel):
    id: uuid.UUID
    word_count: int
    speaker_map: dict[str, Any]
    has_normalized: bool


class MeetingResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    created_by: uuid.UUID
    title: str
    source: str
    status: str
    meeting_date: str | None
    duration_seconds: int | None
    processing_meta: dict[str, Any]
    created_at: str
    updated_at: str


class MeetingDetailResponse(MeetingResponse):
                                                 
    transcript: TranscriptResponse | None = None


class MeetingListResponse(BaseModel):
    meetings: list[MeetingResponse]
    has_next: bool
    next_cursor: str | None


class MeetingCreatedResponse(BaseModel):
    meeting: MeetingResponse
    message: str = "Meeting uploaded successfully. Processing started."


class MeetingRetryResponse(BaseModel):
    meeting: MeetingResponse
    message: str = "Extraction retry started."


                                             
         
                                             

def map_meeting_to_response(meeting: Any) -> MeetingResponse:
    return MeetingResponse(
        id=meeting.id,
        org_id=meeting.org_id,
        created_by=meeting.created_by,
        title=meeting.title,
        source=meeting.source,
        status=meeting.status,
        meeting_date=meeting.meeting_date.isoformat() if meeting.meeting_date else None,
        duration_seconds=meeting.duration_seconds,
        processing_meta=meeting.processing_meta or {},
        created_at=meeting.created_at.isoformat(),
        updated_at=meeting.updated_at.isoformat(),
    )


def map_transcript_to_response(transcript: Any) -> TranscriptResponse:
    return TranscriptResponse(
        id=transcript.id,
        word_count=transcript.word_count,
        speaker_map=transcript.speaker_map or {},
        has_normalized=transcript.normalized_s3_key is not None,
    )
