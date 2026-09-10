   
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


                                                                   
class ProcessingStatus:
    UPLOADED    = "uploaded"                                     
    QUEUED      = "queued"                         
    PROCESSING  = "processing"                      
    COMPLETED   = "completed"                        
    FAILED      = "failed"                             

                       
    TRANSITIONS: dict[str, list[str]] = {
        UPLOADED:    [QUEUED],
        QUEUED:      [PROCESSING, FAILED],
        PROCESSING:  [COMPLETED, FAILED],
        COMPLETED:   [],                     
        FAILED:      [QUEUED],                         
    }

    @classmethod
    def can_transition(cls, current: str, next_status: str) -> bool:
        return next_status in cls.TRANSITIONS.get(current, [])


class MeetingSource:
    ZOOM   = "zoom"
    MEET   = "meet"
    TEAMS  = "teams"
    MANUAL = "manual"
    UPLOAD = "upload"
    PASTE  = "paste"

    ALL = {ZOOM, MEET, TEAMS, MANUAL, UPLOAD, PASTE}


@dataclass
class Meeting:
       
    id: uuid.UUID
    org_id: uuid.UUID
    created_by: uuid.UUID                                         
    title: str
    source: str                                                  
    status: str                                                     
    meeting_date: datetime | None = None
    duration_seconds: int | None = None
    participant_ids: list[uuid.UUID] = field(default_factory=list)
    processing_meta: dict[str, Any] = field(default_factory=dict)
                                                                                  
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_processing(self) -> bool:
        return self.status in (ProcessingStatus.QUEUED, ProcessingStatus.PROCESSING)

    @property
    def is_complete(self) -> bool:
        return self.status == ProcessingStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == ProcessingStatus.FAILED

    def transition_status(self, new_status: str) -> None:
                                                             
        from app.domains.meetings.domain.exceptions import InvalidStatusTransitionError
        if not ProcessingStatus.can_transition(self.status, new_status):
            raise InvalidStatusTransitionError(
                f"Cannot transition meeting from '{self.status}' to '{new_status}'"
            )
        self.status = new_status
        self.updated_at = _now()

    def set_stage(self, stage: int, stage_name: str) -> None:
                                                                 
        self.processing_meta["current_stage"] = stage
        self.processing_meta["current_stage_name"] = stage_name
        self.updated_at = _now()

    def record_error(self, error: str, stage: int | None = None) -> None:
                                            
        self.processing_meta["error"] = error
        if stage is not None:
            self.processing_meta["failed_at_stage"] = stage
        self.updated_at = _now()


@dataclass
class Transcript:
       
    id: uuid.UUID
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    raw_s3_key: str                                              
    normalized_s3_key: str | None = None                                      
    raw_text: str | None = None                                              
    content_hash: str | None = None                                          
    word_count: int = 0
    speaker_map: dict[str, str] = field(default_factory=dict)
                                                                  
    created_at: datetime = field(default_factory=_now)

    @staticmethod
    def compute_hash(text: str) -> str:
                                                                            
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
