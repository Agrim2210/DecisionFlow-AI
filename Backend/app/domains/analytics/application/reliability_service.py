   
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.domains.analytics.domain.entities import UserReliabilitySnapshot
from app.domains.analytics.domain.repositories import ISnapshotRepository

logger = structlog.get_logger(__name__)


class ReliabilityService:

    def __init__(
        self,
        snapshot_repo: ISnapshotRepository,
        db: Any = None,                                                 
    ) -> None:
        self._snapshots = snapshot_repo
        self._db = db

                                                                     

    async def compute_for_user(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> UserReliabilitySnapshot:
           
        stats = await self._fetch_task_stats(user_id, org_id)
        snapshot = self._build_snapshot(user_id, org_id, stats)

                          
        saved = await self._snapshots.upsert(snapshot)

                                                        
        await self._update_user_score(user_id, snapshot.reliability_score)

        logger.debug(
            "reliability_computed",
            user_id=str(user_id),
            score=snapshot.reliability_score,
            assigned=snapshot.tasks_assigned,
            on_time=snapshot.tasks_on_time,
        )
        return saved

                                                                     

    async def refresh_org(self, org_id: uuid.UUID) -> int:
           
        if not self._db:
            logger.warning("reliability_refresh_no_db", org_id=str(org_id))
            return 0

        from sqlalchemy import select
        from app.domains.identity.infra.orm_models import UserORM

        result = await self._db.execute(
            select(UserORM.id).where(
                UserORM.org_id == org_id,
                UserORM.is_active.is_(True),
                UserORM.deleted_at.is_(None),
            )
        )
        user_ids = [row[0] for row in result.fetchall()]

        updated = 0
        for user_id in user_ids:
            try:
                await self.compute_for_user(user_id, org_id)
                updated += 1
            except Exception as exc:
                logger.error(
                    "reliability_refresh_failed",
                    user_id=str(user_id),
                    org_id=str(org_id),
                    error=str(exc),
                )

        logger.info("reliability_refresh_complete", org_id=str(org_id), updated=updated)
        return updated

                                                                    

    async def get_trend(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> list[UserReliabilitySnapshot]:
                                                                    
        return await self._snapshots.get_trend(user_id, org_id, days)

    async def get_latest(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> UserReliabilitySnapshot | None:
                                                         
        return await self._snapshots.get_latest(user_id, org_id)

    async def get_all_latest(
        self, org_id: uuid.UUID
    ) -> list[UserReliabilitySnapshot]:
                                                                                      
        return await self._snapshots.list_by_org(org_id, limit=500)

                                                                    

    async def _fetch_task_stats(
        self, user_id: uuid.UUID, org_id: uuid.UUID
    ) -> dict:
           
        if not self._db:
            return {
                "assigned": 0, "completed": 0,
                "on_time": 0, "overdue": 0, "cancelled": 0,
            }

        from sqlalchemy import select
        from app.domains.extraction.infra.orm_models import ActionItemORM

        result = await self._db.execute(
            select(
                ActionItemORM.status,
                ActionItemORM.due_date,
                ActionItemORM.completed_at,
            ).where(
                ActionItemORM.owner_id == user_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
        )
        rows = result.fetchall()

        assigned   = 0
        completed  = 0
        on_time    = 0
        overdue    = 0
        cancelled  = 0

        for row in rows:
            status       = row.status
            due_date     = row.due_date
            completed_at = row.completed_at

            if status == "cancelled":
                cancelled += 1
                continue                                                

            assigned += 1

            if status == "completed":
                completed += 1
                                                                          
                if due_date is None:
                    on_time += 1
                elif completed_at and completed_at <= due_date:
                    on_time += 1
            elif status == "overdue":
                overdue += 1

        return {
            "assigned":  assigned,
            "completed": completed,
            "on_time":   on_time,
            "overdue":   overdue,
            "cancelled": cancelled,
        }

    def _build_snapshot(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        stats: dict,
    ) -> UserReliabilitySnapshot:
                                                                      
        assigned = stats["assigned"]
        on_time  = stats["on_time"]

                      
        if assigned == 0:
            score = 100.0                                        
        else:
            score = round((on_time / assigned) * 100, 2)

        return UserReliabilitySnapshot(
            id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            snapshot_date=datetime.now(timezone.utc),
            tasks_assigned=assigned,
            tasks_completed=stats["completed"],
            tasks_on_time=on_time,
            tasks_overdue=stats["overdue"],
            tasks_cancelled=stats["cancelled"],
            reliability_score=score,
        )

    async def _update_user_score(
        self, user_id: uuid.UUID, score: float
    ) -> None:
           
        if not self._db:
            return
        try:
            from sqlalchemy import update
            from app.domains.identity.infra.orm_models import UserORM
            await self._db.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(reliability_score=score)
            )
        except Exception as exc:
            logger.warning("user_score_update_failed", user_id=str(user_id), error=str(exc))
