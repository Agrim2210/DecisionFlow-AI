   
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.extraction.domain.entities import MemoryChunk
from app.domains.extraction.domain.repositories import IMemoryRepository
from app.domains.extraction.infra.orm_models import MemoryChunkORM


                                                                     

def _to_entity(orm: MemoryChunkORM) -> MemoryChunk:
    return MemoryChunk(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        source_type=orm.source_type,
        source_id=orm.source_id,
        content=orm.content,
        embedding=list(orm.embedding) if orm.embedding is not None else [],
        metadata=dict(orm.meta_data or {}),
        created_at=orm.created_at,
    )


                                                                      

class SQLMemoryRepository(IMemoryRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, chunks: list[MemoryChunk]) -> None:
           
        for chunk in chunks:
            orm = MemoryChunkORM(
                id=chunk.id,
                org_id=chunk.org_id,
                meeting_id=chunk.meeting_id,
                source_type=chunk.source_type,
                source_id=chunk.source_id,
                content=chunk.content,
                embedding=chunk.embedding,
                meta_data=chunk.metadata,
            )
            self._db.add(orm)
        await self._db.flush()

    async def semantic_search(
        self,
        org_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 10,
        source_type: str | None = None,
    ) -> list[MemoryChunk]:
           
        try:
                                                    
                                                        
            q = (
                select(MemoryChunkORM)
                .where(
                    MemoryChunkORM.org_id == org_id,                                   
                )
            )
            if source_type:
                q = q.where(MemoryChunkORM.source_type == source_type)

                                                                       
            q = q.order_by(
                MemoryChunkORM.embedding.cosine_distance(query_embedding)
            ).limit(limit)

            result = await self._db.execute(q)
            chunks = [_to_entity(r) for r in result.scalars().all()]

                                                                         
            return [c for c in chunks if c.org_id == org_id]

        except Exception as exc:
                                                                        
                                                      
            import structlog
            structlog.get_logger(__name__).warning(
                "semantic_search_failed",
                org_id=str(org_id),
                error=str(exc),
            )
            return []

    async def keyword_search(
        self,
        org_id: uuid.UUID,
        query_text: str,
        limit: int = 10,
        source_type: str | None = None,
    ) -> list[MemoryChunk]:
           
        q = (
            select(MemoryChunkORM)
            .where(
                MemoryChunkORM.org_id == org_id,                          
                MemoryChunkORM.content.ilike(f"%{query_text}%"),
            )
        )
        if source_type:
            q = q.where(MemoryChunkORM.source_type == source_type)

        q = q.order_by(MemoryChunkORM.created_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_to_entity(r) for r in result.scalars().all()]

    async def get_by_source(
        self,
        source_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> list[MemoryChunk]:
           
        result = await self._db.execute(
            select(MemoryChunkORM).where(
                MemoryChunkORM.source_id == source_id,
                MemoryChunkORM.org_id == org_id,
            )
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def delete_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> None:
           
        await self._db.execute(
            delete(MemoryChunkORM).where(
                MemoryChunkORM.meeting_id == meeting_id,
                MemoryChunkORM.org_id == org_id,
            )
        )

    async def delete_by_source(
        self, source_id: uuid.UUID, org_id: uuid.UUID
    ) -> None:
           
        await self._db.execute(
            delete(MemoryChunkORM).where(
                MemoryChunkORM.source_id == source_id,
                MemoryChunkORM.org_id == org_id,
            )
        )
