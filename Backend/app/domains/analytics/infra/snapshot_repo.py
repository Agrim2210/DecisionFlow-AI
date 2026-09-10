   
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.domain.entities import UserReliabilitySnapshot
from app.domains.analytics.domain.repositories import ISnapshotRepository
from app.domains.analytics.infra.orm_models import UserReliabilitySnapshotORM


                                                                     

def _to_entity(orm: UserReliabilitySnapshotORM) -> UserReliabilitySnapshot:
    return UserReliabilitySnapshot(
        id=orm.id,
        org_id=orm.org_id,
        user_id=orm.user_id,
        snapshot_date=orm.snapshot_date,
        tasks_assigned=orm.tasks_assigned,
        tasks_completed=orm.tasks_completed,
        tasks_on_time=orm.tasks_on_time,
        tasks_overdue=orm.tasks_overdue,
        tasks_cancelled=orm.tasks_cancelled,
        reliability_score=float(orm.reliability_score),
        created_at=orm.created_at,
    )


                                                                      

class SQLSnapshotRepository(ISnapshotRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(
        self, snapshot: UserReliabilitySnapshot
    ) -> UserReliabilitySnapshot:
           
        existing = await self.get_latest(snapshot.user_id, snapshot.org_id)

        if existing:
                                 
            result = await self._db.execute(
                select(UserReliabilitySnapshotORM).where(
                    UserReliabilitySnapshotORM.id == existing.id
                )
            )
            orm = result.scalar_one()
            orm.snapshot_date    = snapshot.snapshot_date
            orm.tasks_assigned   = snapshot.tasks_assigned
            orm.tasks_completed  = snapshot.tasks_completed
            orm.tasks_on_time    = snapshot.tasks_on_time
            orm.tasks_overdue    = snapshot.tasks_overdue
            orm.tasks_cancelled  = snapshot.tasks_cancelled
            orm.reliability_score = snapshot.reliability_score
            await self._db.flush()
            return _to_entity(orm)
        else:
                            
            orm = UserReliabilitySnapshotORM(
                id=snapshot.id,
                org_id=snapshot.org_id,
                user_id=snapshot.user_id,
                snapshot_date=snapshot.snapshot_date,
                tasks_assigned=snapshot.tasks_assigned,
                tasks_completed=snapshot.tasks_completed,
                tasks_on_time=snapshot.tasks_on_time,
                tasks_overdue=snapshot.tasks_overdue,
                tasks_cancelled=snapshot.tasks_cancelled,
                reliability_score=snapshot.reliability_score,
            )
            self._db.add(orm)
            await self._db.flush()
            await self._db.refresh(orm)
            return _to_entity(orm)

    async def get_latest(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> UserReliabilitySnapshot | None:
           
        result = await self._db.execute(
            select(UserReliabilitySnapshotORM)
            .where(
                UserReliabilitySnapshotORM.user_id == user_id,
                UserReliabilitySnapshotORM.org_id == org_id,
            )
            .order_by(UserReliabilitySnapshotORM.snapshot_date.desc())
            .limit(1)
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 200,
    ) -> list[UserReliabilitySnapshot]:
           
                                                             
        subq = (
            select(
                UserReliabilitySnapshotORM.user_id,
                func.max(UserReliabilitySnapshotORM.snapshot_date).label("max_date"),
            )
            .where(UserReliabilitySnapshotORM.org_id == org_id)
            .group_by(UserReliabilitySnapshotORM.user_id)
            .subquery()
        )

        result = await self._db.execute(
            select(UserReliabilitySnapshotORM)
            .join(
                subq,
                (UserReliabilitySnapshotORM.user_id == subq.c.user_id)
                & (UserReliabilitySnapshotORM.snapshot_date == subq.c.max_date),
            )
            .where(UserReliabilitySnapshotORM.org_id == org_id)
            .order_by(UserReliabilitySnapshotORM.reliability_score.desc())
            .limit(limit)
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def get_trend(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> list[UserReliabilitySnapshot]:
           
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._db.execute(
            select(UserReliabilitySnapshotORM)
            .where(
                UserReliabilitySnapshotORM.user_id == user_id,
                UserReliabilitySnapshotORM.org_id == org_id,
                UserReliabilitySnapshotORM.snapshot_date >= cutoff,
            )
            .order_by(UserReliabilitySnapshotORM.snapshot_date.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def bulk_upsert(
        self, snapshots: list[UserReliabilitySnapshot]
    ) -> int:
           
        count = 0
        for snap in snapshots:
            await self.upsert(snap)
            count += 1
        return count

    async def delete_old(
        self,
        org_id: uuid.UUID,
        before: datetime,
    ) -> int:
           
        from sqlalchemy import delete as sa_delete
        result = await self._db.execute(
            sa_delete(UserReliabilitySnapshotORM).where(
                UserReliabilitySnapshotORM.org_id == org_id,
                UserReliabilitySnapshotORM.snapshot_date < before,
            )
        )
        return result.rowcount                              
