from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.domains.search.application.queries import (
    DeleteMeetingIndexQuery,
    IndexEntityQuery,
    IndexMeetingQuery,
)
from app.domains.search.domain.entities import MemoryChunk

logger = structlog.get_logger(__name__)


class MemoryService:
       

    def __init__(self, memory_repo: Any, embed_client: Any = None) -> None:
        self._memory = memory_repo
        self._embed = embed_client

    async def index_meeting(self, query: IndexMeetingQuery) -> int:
           
        await self._memory.delete_by_meeting(query.meeting_id, query.org_id)

        texts: list[str] = []
        meta: list[dict] = []

        for d in query.decisions:
            text = f"Decision: {d.get('title', '')}. {d.get('description', '')}"
            texts.append(text)
            meta.append({
                "source_type": "decision",
                "source_id": str(d["id"]),
                "title": d.get("title", ""),
                "decision_type": d.get("decision_type", ""),
            })

        for t in query.action_items:
            owner = f" Owner: {t.get('owner_name', '')}." if t.get("owner_name") else ""
            due = f" Due: {t.get('deadline_text', '')}." if t.get("deadline_text") else ""
            text = f"Task: {t.get('title', '')}.{owner}{due} {t.get('description', '')}"
            texts.append(text)
            meta.append({
                "source_type": "action_item",
                "source_id": str(t["id"]),
                "title": t.get("title", ""),
                "priority": t.get("priority", "medium"),
                "status": t.get("status", "pending"),
            })

        if not texts:
            return 0

        if not self._embed:
            logger.warning("memory_index_skipped", reason="no_embed_client")
            return 0

        try:
            embed_resp = await self._embed.embed(texts)
            embeddings = embed_resp.embeddings
        except Exception as exc:
            logger.error("memory_embed_failed", error=str(exc))
            return 0

        chunks: list[MemoryChunk] = []
        for i, (text, m, embedding) in enumerate(zip(texts, meta, embeddings)):
            chunks.append(MemoryChunk(
                id=uuid.uuid4(),
                org_id=query.org_id,
                meeting_id=query.meeting_id,
                source_type=m["source_type"],
                source_id=uuid.UUID(m["source_id"]),
                content=text,
                embedding=embedding,
                metadata=m,
            ))

        await self._memory.bulk_create(chunks)

        logger.info(
            "meeting_indexed",
            meeting_id=str(query.meeting_id),
            org_id=str(query.org_id),
            chunks=len(chunks),
        )
        return len(chunks)

    async def index_entity(self, query: IndexEntityQuery) -> bool:
           
        if not self._embed:
            return False

        await self._memory.delete_by_source(query.source_id, query.org_id)

        try:
            embed_resp = await self._embed.embed([query.content])
            if not embed_resp.embeddings:
                return False
            embedding = embed_resp.embeddings[0]
        except Exception as exc:
            logger.warning("entity_embed_failed", source_id=str(query.source_id), error=str(exc))
            return False

        chunk = MemoryChunk(
            id=uuid.uuid4(),
            org_id=query.org_id,
            meeting_id=query.meeting_id,
            source_type=query.source_type,
            source_id=query.source_id,
            content=query.content,
            embedding=embedding,
            metadata=query.metadata,
        )
        await self._memory.bulk_create([chunk])
        return True

    async def delete_meeting_index(self, query: DeleteMeetingIndexQuery) -> None:
                                                             
        await self._memory.delete_by_meeting(query.meeting_id, query.org_id)
        logger.info(
            "meeting_index_deleted",
            meeting_id=str(query.meeting_id),
            org_id=str(query.org_id),
        )
