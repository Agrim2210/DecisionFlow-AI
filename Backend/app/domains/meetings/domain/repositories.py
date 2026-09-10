   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domains.meetings.domain.entities import Meeting, Transcript


class IMeetingRepository(ABC):

    @abstractmethod
    async def create(self, meeting: Meeting) -> Meeting: ...

    @abstractmethod
    async def get_by_id(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> Meeting | None: ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,                                                 
        status: str | None = None,
    ) -> list[Meeting]: ...

    @abstractmethod
    async def update(self, meeting: Meeting) -> Meeting: ...

    @abstractmethod
    async def soft_delete(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def exists_by_content_hash(self, content_hash: str, org_id: uuid.UUID) -> Meeting | None:
                                                                                  
        ...


class ITranscriptRepository(ABC):

    @abstractmethod
    async def create(self, transcript: Transcript) -> Transcript: ...

    @abstractmethod
    async def get_by_meeting_id(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> Transcript | None: ...

    @abstractmethod
    async def update(self, transcript: Transcript) -> Transcript: ...
