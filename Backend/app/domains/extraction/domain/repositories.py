   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domains.extraction.domain.entities import (
    ActionItem,
    Decision,
    MemoryChunk,
    OpenQuestion,
    Risk,
)


class IDecisionRepository(ABC):

    @abstractmethod
    async def bulk_create(self, decisions: list[Decision]) -> list[Decision]: ...

    @abstractmethod
    async def get_by_id(self, decision_id: uuid.UUID, org_id: uuid.UUID) -> Decision | None: ...

    @abstractmethod
    async def list_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> list[Decision]: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        decision_type: str | None = None,
        status: str | None = None,
    ) -> list[Decision]: ...

    @abstractmethod
    async def update(self, decision: Decision) -> Decision: ...

    @abstractmethod
    async def bulk_upsert_embeddings(
        self, items: list[tuple[uuid.UUID, list[float]]]
    ) -> None:
                                                                     
        ...


class IActionItemRepository(ABC):

    @abstractmethod
    async def bulk_create(self, items: list[ActionItem]) -> list[ActionItem]: ...

    @abstractmethod
    async def get_by_id(self, item_id: uuid.UUID, org_id: uuid.UUID) -> ActionItem | None: ...

    @abstractmethod
    async def list_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> list[ActionItem]: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,                                    
        status: str | None = None,
        overdue_only: bool = False,
    ) -> list[ActionItem]: ...

    @abstractmethod
    async def update(self, item: ActionItem) -> ActionItem: ...

    @abstractmethod
    async def get_overdue(self, org_id: uuid.UUID, as_of: datetime) -> list[ActionItem]:
                                                  
        ...

    @abstractmethod
    async def bulk_upsert_embeddings(
        self, items: list[tuple[uuid.UUID, list[float]]]
    ) -> None: ...


class IRiskRepository(ABC):

    @abstractmethod
    async def bulk_create(self, risks: list[Risk]) -> list[Risk]: ...

    @abstractmethod
    async def get_by_id(self, risk_id: uuid.UUID, org_id: uuid.UUID) -> Risk | None: ...

    @abstractmethod
    async def list_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> list[Risk]: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Risk]: ...

    @abstractmethod
    async def update(self, risk: Risk) -> Risk: ...


class IOpenQuestionRepository(ABC):

    @abstractmethod
    async def bulk_create(self, questions: list[OpenQuestion]) -> list[OpenQuestion]: ...

    @abstractmethod
    async def get_by_id(self, qid: uuid.UUID, org_id: uuid.UUID) -> OpenQuestion | None: ...

    @abstractmethod
    async def list_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> list[OpenQuestion]: ...

    @abstractmethod
    async def update(self, question: OpenQuestion) -> OpenQuestion: ...


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
    ) -> list[MemoryChunk]:
           
        ...

    @abstractmethod
    async def delete_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> None: ...
