   
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from app.domains.graph.domain.entities import TaskDependency


class IDependencyRepository(ABC):

    @abstractmethod
    async def create(self, dep: TaskDependency) -> TaskDependency:
                                            
        ...

    @abstractmethod
    async def bulk_create(self, deps: list[TaskDependency]) -> list[TaskDependency]:
                                                                                   
        ...

    @abstractmethod
    async def get_by_id(
        self, dep_id: uuid.UUID, org_id: uuid.UUID
    ) -> TaskDependency | None:
                                           
        ...

    @abstractmethod
    async def list_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[TaskDependency]:
           
        ...

    @abstractmethod
    async def list_for_task(
        self, task_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[TaskDependency]:
           
        ...

    @abstractmethod
    async def get_all_for_org(self, org_id: uuid.UUID) -> list[TaskDependency]:
           
        ...

    @abstractmethod
    async def exists(
        self,
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> bool:
                                                                                 
        ...

    @abstractmethod
    async def delete(self, dep_id: uuid.UUID, org_id: uuid.UUID) -> bool:
           
        ...
