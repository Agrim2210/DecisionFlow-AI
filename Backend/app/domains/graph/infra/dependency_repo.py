   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.graph.domain.entities import TaskDependency
from app.domains.graph.domain.repositories import IDependencyRepository
from app.domains.graph.infra.orm_models import TaskDependencyORM


                                                                     

def _to_entity(orm: TaskDependencyORM) -> TaskDependency:
    return TaskDependency(
        id=orm.id,
        org_id=orm.org_id,
        upstream_id=orm.upstream_id,
        downstream_id=orm.downstream_id,
        dependency_type=orm.dependency_type,
        detected_by=orm.detected_by,
        confidence_score=float(orm.confidence_score),
        created_by=orm.created_by,
        created_at=orm.created_at,
    )


                                                                      

class SQLDependencyRepository(IDependencyRepository):
       

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, dep: TaskDependency) -> TaskDependency:
           
        orm = TaskDependencyORM(
            id=dep.id,
            org_id=dep.org_id,
            upstream_id=dep.upstream_id,
            downstream_id=dep.downstream_id,
            dependency_type=dep.dependency_type,
            detected_by=dep.detected_by,
            confidence_score=dep.confidence_score,
            created_by=dep.created_by,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _to_entity(orm)

    async def bulk_create(self, deps: list[TaskDependency]) -> list[TaskDependency]:
           
        orm_objects: list[TaskDependencyORM] = []
        for dep in deps:
            orm = TaskDependencyORM(
                id=dep.id,
                org_id=dep.org_id,
                upstream_id=dep.upstream_id,
                downstream_id=dep.downstream_id,
                dependency_type=dep.dependency_type,
                detected_by=dep.detected_by,
                confidence_score=dep.confidence_score,
                created_by=dep.created_by,
            )
            self._db.add(orm)
            orm_objects.append(orm)

        await self._db.flush()
        return [_to_entity(o) for o in orm_objects]

    async def get_by_id(
        self, dep_id: uuid.UUID, org_id: uuid.UUID
    ) -> TaskDependency | None:
        result = await self._db.execute(
            select(TaskDependencyORM).where(
                TaskDependencyORM.id == dep_id,
                TaskDependencyORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[TaskDependency]:
           
        from app.domains.extraction.infra.orm_models import ActionItemORM

        result = await self._db.execute(
            select(TaskDependencyORM)
            .join(
                ActionItemORM,
                ActionItemORM.id == TaskDependencyORM.upstream_id,
            )
            .where(
                ActionItemORM.meeting_id == meeting_id,
                TaskDependencyORM.org_id == org_id,
            )
            .order_by(TaskDependencyORM.created_at.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_for_task(
        self, task_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[TaskDependency]:
           
        result = await self._db.execute(
            select(TaskDependencyORM).where(
                TaskDependencyORM.org_id == org_id,
                (
                    (TaskDependencyORM.upstream_id == task_id) |
                    (TaskDependencyORM.downstream_id == task_id)
                ),
            ).order_by(TaskDependencyORM.created_at.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def get_all_for_org(self, org_id: uuid.UUID) -> list[TaskDependency]:
           
        result = await self._db.execute(
            select(TaskDependencyORM).where(
                TaskDependencyORM.org_id == org_id,
            ).order_by(TaskDependencyORM.created_at.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def exists(
        self,
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> bool:
           
        result = await self._db.execute(
            select(TaskDependencyORM.id).where(
                TaskDependencyORM.upstream_id == upstream_id,
                TaskDependencyORM.downstream_id == downstream_id,
                TaskDependencyORM.org_id == org_id,
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def delete(self, dep_id: uuid.UUID, org_id: uuid.UUID) -> bool:
           
        result = await self._db.execute(
            delete(TaskDependencyORM).where(
                TaskDependencyORM.id == dep_id,
                TaskDependencyORM.org_id == org_id,
            )
        )
        return result.rowcount > 0                              
