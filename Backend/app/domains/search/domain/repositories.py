from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from app.domains.search.domain.entities import MemoryChunk


class IMemoryRepository(ABC):

    @abstractmethod
    async def bulk_create(self, chunks: list[MemoryChunk]) -> None: ...

    @abstractmethod
    async def semantic_search(
        self,
        org_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 10,
        source_type: str | None = None,
        meeting_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[MemoryChunk]: ...

    @abstractmethod
    async def keyword_search(
        self,
        org_id: uuid.UUID,
        query_text: str,
        limit: int = 10,
        source_type: str | None = None,
        meeting_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[MemoryChunk]: ...

    @abstractmethod
    async def prefix_search(
        self,
        org_id: uuid.UUID,
        prefix: str,
        source_type: str | None = None,
        limit: int = 5,
    ) -> list[MemoryChunk]: ...

    @abstractmethod
    async def get_by_source(
        self, source_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[MemoryChunk]: ...

    @abstractmethod
    async def delete_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> None: ...

    @abstractmethod
    async def delete_by_source(
        self, source_id: uuid.UUID, org_id: uuid.UUID
    ) -> None: ...
