   
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


                                                                 
                 
                                                                 

class SearchRequest(BaseModel):
       
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query",
        examples=["API architecture decision", "Rahul overdue tasks", "authentication approach"],
    )
    mode: str = Field(
        default="hybrid",
        pattern=r"^(semantic|keyword|hybrid)$",
        description=(
            "Search mode. "
            "semantic=vector similarity, "
            "keyword=exact text match, "
            "hybrid=best of both (recommended)"
        ),
    )
    source_type: str | None = Field(
        default=None,
        pattern=r"^(meeting|decision|action_item|risk|question)$",
        description="Narrow results to a specific entity type",
    )
    meeting_id: uuid.UUID | None = Field(
        default=None,
        description="Narrow results to a specific meeting",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return",
    )
    date_from: datetime | None = Field(
        default=None,
        description="Only return content created after this datetime (ISO 8601)",
    )
    date_to: datetime | None = Field(
        default=None,
        description="Only return content created before this datetime (ISO 8601)",
    )
    min_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score threshold (0.0–1.0). Filters low-quality matches.",
    )

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


class MeetingSemanticSearchRequest(BaseModel):
                                                                     
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language query about this meeting",
        examples=["What was decided about the release date?"],
    )
    source_type: str | None = Field(
        default=None,
        pattern=r"^(meeting|decision|action_item|risk|question)$",
        description="Optionally narrow the search to one type of meeting content",
    )
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, v: str) -> str:
        return v.strip()


                                                                 
                  
                                                                 

class SearchResultItemResponse(BaseModel):
       
    source_id: uuid.UUID
    source_type: str
    meeting_id: uuid.UUID
    content: str
    score: float = Field(description="Relevance score 0.0–1.0")
    title: str = Field(description="Entity title for display")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context: status, priority, owner_id, etc.",
    )


class SearchHighlightResponse(BaseModel):
       
    snippet: str                                          
    matched_terms: list[str]                                   


class SearchResultResponse(BaseModel):
       
    items: list[SearchResultItemResponse]
    total_found: int
    query: str
    mode: str
    took_ms: float


class SuggestRequest(BaseModel):
       
    prefix: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Search prefix for autocomplete",
    )
    source_type: str | None = Field(
        default=None,
        pattern=r"^(meeting|decision|action_item|risk|question)$",
    )
    limit: int = Field(default=5, ge=1, le=10)

    @field_validator("prefix", mode="before")
    @classmethod
    def strip_prefix(cls, v: str) -> str:
        return v.strip()


class SuggestionResponse(BaseModel):
                                           
    source_id: uuid.UUID
    source_type: str
    title: str
    meeting_id: uuid.UUID


class SuggestResponse(BaseModel):
                                            
    suggestions: list[SuggestionResponse]
    prefix: str


                                                                 
         
                                                                 

def map_search_result(result: Any) -> SearchResultResponse:
                                                                       
    return SearchResultResponse(
        items=[
            SearchResultItemResponse(
                source_id=item.source_id,
                source_type=item.source_type,
                meeting_id=item.meeting_id,
                content=item.content,
                score=round(float(item.score), 4),
                title=item.title or "",
                metadata=item.metadata or {},
            )
            for item in result.items
        ],
        total_found=result.total_found,
        query=result.query,
        mode=result.mode,
        took_ms=result.took_ms,
    )


def map_suggestions(suggestions: list[Any], prefix: str) -> SuggestResponse:
                                                                        
    return SuggestResponse(
        suggestions=[
            SuggestionResponse(
                source_id=s.source_id,
                source_type=s.source_type,
                title=s.metadata.get("title", str(s.source_id)),
                meeting_id=s.meeting_id,
            )
            for s in suggestions
        ],
        prefix=prefix,
    )
