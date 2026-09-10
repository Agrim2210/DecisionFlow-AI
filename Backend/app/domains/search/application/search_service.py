   
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.domains.search.application.queries import SearchQuery, SuggestQuery
from app.domains.search.domain.entities import MemoryChunk, SearchMode

logger = structlog.get_logger(__name__)

                                        
_RRF_K = 60


@dataclass
class SearchResultItem:
                                      
    source_id: uuid.UUID
    source_type: str
    meeting_id: uuid.UUID
    content: str
    score: float
    title: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
                                                             
    query: str
    mode: str
    items: list[SearchResultItem]
    total_found: int
    took_ms: float


class SearchService:
       

    def __init__(
        self,
        memory_repo: Any,                          
        embed_client: Any = None,                                               
    ) -> None:
        self._memory = memory_repo
        self._embed = embed_client

                                                                    
            
                                                                    

    async def search(self, query: SearchQuery) -> SearchResult:
           
        t0 = time.perf_counter()

        mode = query.mode

                                               
        if mode in (SearchMode.SEMANTIC, SearchMode.HYBRID) and not self._embed:
            logger.debug("search_degraded_to_keyword", reason="no_embed_client")
            mode = SearchMode.KEYWORD

        semantic_items: list[SearchResultItem] = []
        keyword_items: list[SearchResultItem] = []

                                                                     
        if mode in (SearchMode.SEMANTIC, SearchMode.HYBRID):
            semantic_items = await self._semantic_search(query)

                                                                     
        if mode in (SearchMode.KEYWORD, SearchMode.HYBRID):
            keyword_items = await self._keyword_search(query)

                                                                     
        if mode == SearchMode.HYBRID:
            items = self._rrf_merge(semantic_items, keyword_items, limit=query.limit)
        elif mode == SearchMode.SEMANTIC:
            items = semantic_items[: query.limit]
        else:
            items = keyword_items[: query.limit]

                                                                     
        if query.min_score is not None:
            items = [i for i in items if i.score >= query.min_score]

        took_ms = round((time.perf_counter() - t0) * 1000, 2)

        logger.info(
            "search_complete",
            org_id=str(query.org_id),
            mode=mode,
            query_len=len(query.text),
            results=len(items),
            took_ms=took_ms,
        )

        return SearchResult(
            query=query.text,
            mode=mode,
            items=items,
            total_found=len(items),
            took_ms=took_ms,
        )

                                                                     

    async def _semantic_search(
        self, query: SearchQuery
    ) -> list[SearchResultItem]:
           
        try:
            embed_resp = await self._embed.embed([query.text])
            if not embed_resp.embeddings:
                logger.warning("embed_returned_empty", query=query.text[:50])
                return []
            query_embedding = embed_resp.embeddings[0]
        except Exception as exc:
            logger.warning("embed_query_failed", error=str(exc))
            return []

        try:
            chunks = await self._memory.semantic_search(
                org_id=query.org_id,
                query_embedding=query_embedding,
                limit=query.limit * 3,                                 
                source_type=query.source_type,
                meeting_id=query.meeting_id,
                date_from=query.date_from,
                date_to=query.date_to,
            )
        except Exception as exc:
            logger.warning("semantic_search_failed", error=str(exc))
            return []

        return [
            SearchResultItem(
                source_id=chunk.source_id,
                source_type=chunk.source_type,
                meeting_id=chunk.meeting_id,
                content=chunk.content,
                score=round(1.0 / (i + 1), 6),                     
                title=chunk.metadata.get("title", ""),
                metadata=chunk.metadata or {},
            )
            for i, chunk in enumerate(chunks)
        ]

                                                                     

    async def _keyword_search(
        self, query: SearchQuery
    ) -> list[SearchResultItem]:
           
        try:
            chunks = await self._memory.keyword_search(
                org_id=query.org_id,
                query_text=query.text,
                limit=query.limit * 3,
                source_type=query.source_type,
                meeting_id=query.meeting_id,
                date_from=query.date_from,
                date_to=query.date_to,
            )
        except Exception as exc:
            logger.warning("keyword_search_failed", error=str(exc))
            return []

        return [
            SearchResultItem(
                source_id=chunk.source_id,
                source_type=chunk.source_type,
                meeting_id=chunk.meeting_id,
                content=chunk.content,
                score=round(1.0 / (i + 1), 6),
                title=chunk.metadata.get("title", ""),
                metadata=chunk.metadata or {},
            )
            for i, chunk in enumerate(chunks)
        ]

                                                                     

    @staticmethod
    def _rrf_merge(
        semantic: list[SearchResultItem],
        keyword: list[SearchResultItem],
        limit: int = 10,
        k: int = _RRF_K,
    ) -> list[SearchResultItem]:
           
        scores: dict[uuid.UUID, float] = {}
        items_by_id: dict[uuid.UUID, SearchResultItem] = {}

                                  
        for rank, item in enumerate(semantic):
            rrf_score = 1.0 / (k + rank + 1)
            scores[item.source_id] = scores.get(item.source_id, 0.0) + rrf_score
            items_by_id[item.source_id] = item

                                 
        for rank, item in enumerate(keyword):
            rrf_score = 1.0 / (k + rank + 1)
            scores[item.source_id] = scores.get(item.source_id, 0.0) + rrf_score
            if item.source_id not in items_by_id:
                items_by_id[item.source_id] = item

                                         
        sorted_ids = sorted(scores, key=lambda sid: scores[sid], reverse=True)

        merged: list[SearchResultItem] = []
        for sid in sorted_ids[:limit]:
            item = items_by_id[sid]
                                                          
            item.score = round(scores[sid], 6)
            merged.append(item)

        return merged

                                                                    
                            
                                                                    

    async def suggest(self, query: SuggestQuery) -> list[MemoryChunk]:
           
        try:
            suggestions = await self._memory.prefix_search(
                org_id=query.org_id,
                prefix=query.prefix,
                source_type=query.source_type,
                limit=query.limit,
            )
            logger.debug(
                "suggest_complete",
                org_id=str(query.org_id),
                prefix=query.prefix,
                results=len(suggestions),
            )
            return suggestions
        except Exception as exc:
            logger.warning("suggest_failed", error=str(exc))
            return []
