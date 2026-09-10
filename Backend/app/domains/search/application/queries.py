   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SearchQuery:
       
    org_id: uuid.UUID
    text: str                                                       
    mode: str = "hybrid"                                                 
    limit: int = 10                                                
    source_type: str | None = None                                               
    meeting_id: uuid.UUID | None = None                                 
    date_from: datetime | None = None                                
    date_to: datetime | None = None                                
    min_score: float | None = None                                           


@dataclass(frozen=True)
class SuggestQuery:
       
    org_id: uuid.UUID
    prefix: str                                              
    source_type: str | None = None                                             
    limit: int = 5                                           


@dataclass(frozen=True)
class IndexEntityQuery:
       
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    source_id: uuid.UUID
    source_type: str                                                
    content: str                                           
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class IndexMeetingQuery:
       
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    decisions: list[dict] = field(default_factory=list)
    action_items: list[dict] = field(default_factory=list)
                                                                    


@dataclass(frozen=True)
class DeleteMeetingIndexQuery:
       
    org_id: uuid.UUID
    meeting_id: uuid.UUID
