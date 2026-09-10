from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SearchMode:
    SEMANTIC = "semantic"
    KEYWORD  = "hybrid"
    HYBRID   = "hybrid"
    ALL      = frozenset({"semantic", "keyword", "hybrid"})


class SourceType:
    DECISION    = "decision"
    ACTION_ITEM = "action_item"
    TRANSCRIPT  = "transcript"
    ALL         = frozenset({"decision", "action_item", "transcript"})


@dataclass
class MemoryChunk:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    source_type: str                                         
    source_id: uuid.UUID                                              
    content: str                                                
    embedding: list[float]                                                                      
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    @property
    def title(self) -> str:
        return self.metadata.get("title", "")

    @property
    def is_decision(self) -> bool:
        return self.source_type == SourceType.DECISION

    @property
    def is_action_item(self) -> bool:
        return self.source_type == SourceType.ACTION_ITEM


@dataclass
class SearchResultItem:
                                                              
    source_id: uuid.UUID
    source_type: str
    meeting_id: uuid.UUID
    content: str
    score: float
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_relevance(self) -> bool:
        return self.score >= 0.8

    @property
    def is_low_relevance(self) -> bool:
        return self.score < 0.3


@dataclass
class SearchResult:
                                                           
    query: str
    mode: str
    items: list[SearchResultItem]
    total_found: int
    took_ms: float

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @property
    def top_result(self) -> SearchResultItem | None:
        return self.items[0] if self.items else None
