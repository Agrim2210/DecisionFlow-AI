   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.domains.analytics.domain.entities import (
    MeetingAnalytics,
    UserReliabilitySnapshot,
)


class ISnapshotRepository(ABC):
       

    @abstractmethod
    async def upsert(
        self, snapshot: UserReliabilitySnapshot
    ) -> UserReliabilitySnapshot:
           
        ...

    @abstractmethod
    async def get_latest(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> UserReliabilitySnapshot | None:
           
        ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 200,
    ) -> list[UserReliabilitySnapshot]:
           
        ...

    @abstractmethod
    async def get_trend(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> list[UserReliabilitySnapshot]:
           
        ...

    @abstractmethod
    async def bulk_upsert(
        self, snapshots: list[UserReliabilitySnapshot]
    ) -> int:
           
        ...

    @abstractmethod
    async def delete_old(
        self,
        org_id: uuid.UUID,
        before: datetime,
    ) -> int:
           
        ...


class IMeetingAnalyticsRepository(ABC):
       

    @abstractmethod
    async def upsert(
        self, analytics: MeetingAnalytics
    ) -> MeetingAnalytics:
           
        ...

    @abstractmethod
    async def get_by_meeting(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics | None:
           
        ...

    @abstractmethod
    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 20,
    ) -> list[MeetingAnalytics]:
           
        ...

    @abstractmethod
    async def list_by_meeting_ids(
        self,
        meeting_ids: list[uuid.UUID],
        org_id: uuid.UUID,
    ) -> list[MeetingAnalytics]:
           
        ...

    @abstractmethod
    async def update_execution_rate(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        execution_rate: float,
    ) -> None:
           
        ...
