   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.domain.entities import MeetingAnalytics
from app.domains.analytics.domain.repositories import IMeetingAnalyticsRepository
from app.domains.analytics.infra.orm_models import MeetingAnalyticsORM


                                                                     

def _to_entity(orm: MeetingAnalyticsORM) -> MeetingAnalytics:
    return MeetingAnalytics(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        decisions_count=orm.decisions_count,
        action_items_count=orm.action_items_count,
        unassigned_tasks=orm.unassigned_tasks,
        risks_count=orm.risks_count,
        critical_risks=orm.critical_risks,
        dependencies_count=orm.dependencies_count,
        open_questions_count=orm.open_questions_count,
        execution_rate=float(orm.execution_rate),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


                                                                      

class SQLMeetingAnalyticsRepository(IMeetingAnalyticsRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert(
        self, analytics: MeetingAnalytics
    ) -> MeetingAnalytics:
           
        existing = await self.get_by_meeting(analytics.meeting_id, analytics.org_id)

        if existing:
                                                   
            result = await self._db.execute(
                select(MeetingAnalyticsORM).where(
                    MeetingAnalyticsORM.meeting_id == analytics.meeting_id
                )
            )
            orm = result.scalar_one()
            orm.decisions_count      = analytics.decisions_count
            orm.action_items_count   = analytics.action_items_count
            orm.unassigned_tasks     = analytics.unassigned_tasks
            orm.risks_count          = analytics.risks_count
            orm.critical_risks       = analytics.critical_risks
            orm.dependencies_count   = analytics.dependencies_count
            orm.open_questions_count = analytics.open_questions_count
            orm.execution_rate       = analytics.execution_rate
            orm.updated_at           = datetime.now(timezone.utc)
            await self._db.flush()
            return _to_entity(orm)
        else:
                            
            orm = MeetingAnalyticsORM(
                id=analytics.id,
                org_id=analytics.org_id,
                meeting_id=analytics.meeting_id,
                decisions_count=analytics.decisions_count,
                action_items_count=analytics.action_items_count,
                unassigned_tasks=analytics.unassigned_tasks,
                risks_count=analytics.risks_count,
                critical_risks=analytics.critical_risks,
                dependencies_count=analytics.dependencies_count,
                open_questions_count=analytics.open_questions_count,
                execution_rate=analytics.execution_rate,
            )
            self._db.add(orm)
            await self._db.flush()
            await self._db.refresh(orm)
            return _to_entity(orm)

    async def get_by_meeting(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics | None:
           
        result = await self._db.execute(
            select(MeetingAnalyticsORM).where(
                MeetingAnalyticsORM.meeting_id == meeting_id,
                MeetingAnalyticsORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 20,
    ) -> list[MeetingAnalytics]:
           
        result = await self._db.execute(
            select(MeetingAnalyticsORM)
            .where(MeetingAnalyticsORM.org_id == org_id)
            .order_by(MeetingAnalyticsORM.created_at.desc())
            .limit(limit)
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_by_meeting_ids(
        self,
        meeting_ids: list[uuid.UUID],
        org_id: uuid.UUID,
    ) -> list[MeetingAnalytics]:
           
        if not meeting_ids:
            return []

        result = await self._db.execute(
            select(MeetingAnalyticsORM).where(
                MeetingAnalyticsORM.meeting_id.in_(meeting_ids),
                MeetingAnalyticsORM.org_id == org_id,
            )
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def update_execution_rate(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        execution_rate: float,
    ) -> None:
           
        await self._db.execute(
            sa_update(MeetingAnalyticsORM)
            .where(
                MeetingAnalyticsORM.meeting_id == meeting_id,
                MeetingAnalyticsORM.org_id == org_id,
            )
            .values(
                execution_rate=execution_rate,
                updated_at=datetime.now(timezone.utc),
            )
        )
