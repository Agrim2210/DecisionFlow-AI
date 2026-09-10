   
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.domains.analytics.domain.entities import MeetingAnalytics
from app.domains.analytics.domain.repositories import IMeetingAnalyticsRepository

logger = structlog.get_logger(__name__)


class ROIService:

    def __init__(
        self,
        meeting_analytics_repo: IMeetingAnalyticsRepository,
        db: Any = None,                                               
    ) -> None:
        self._repo = meeting_analytics_repo
        self._db = db

                                                                     

    async def compute_meeting_analytics(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics:
           
        stats = await self._fetch_meeting_stats(meeting_id, org_id)
        analytics = self._build_analytics(meeting_id, org_id, stats)
        saved = await self._repo.upsert(analytics)

        logger.info(
            "meeting_analytics_computed",
            meeting_id=str(meeting_id),
            decisions=saved.decisions_count,
            tasks=saved.action_items_count,
            risks=saved.risks_count,
            execution_rate=saved.execution_rate,
        )
        return saved

    async def get_meeting_analytics(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics:
           
        existing = await self._repo.get_by_meeting(meeting_id, org_id)
        if existing:
                                                               
            updated = await self._refresh_execution_rate(existing, meeting_id, org_id)
            return updated
        return await self.compute_meeting_analytics(meeting_id, org_id)

    async def get_org_meeting_analytics(
        self,
        org_id: uuid.UUID,
        limit: int = 20,
    ) -> list[MeetingAnalytics]:
                                                                     
        return await self._repo.list_by_org(org_id, limit=limit)

                                                                    

    async def compute_org_roi_summary(self, org_id: uuid.UUID) -> dict:
           
        all_analytics = await self._repo.list_by_org(org_id, limit=500)
        if not all_analytics:
            return {
                "total_meetings_analysed": 0,
                "avg_decisions_per_meeting": 0.0,
                "avg_tasks_per_meeting": 0.0,
                "avg_execution_rate": 0.0,
                "total_decisions": 0,
                "total_tasks": 0,
                "total_tasks_unassigned": 0,
            }

        n = len(all_analytics)
        return {
            "total_meetings_analysed":   n,
            "avg_decisions_per_meeting": round(
                sum(a.decisions_count for a in all_analytics) / n, 1
            ),
            "avg_tasks_per_meeting":     round(
                sum(a.action_items_count for a in all_analytics) / n, 1
            ),
            "avg_execution_rate":        round(
                sum(a.execution_rate for a in all_analytics) / n, 2
            ),
            "total_decisions":           sum(a.decisions_count for a in all_analytics),
            "total_tasks":               sum(a.action_items_count for a in all_analytics),
            "total_tasks_unassigned":    sum(a.unassigned_tasks for a in all_analytics),
        }

                                                                    

    async def _fetch_meeting_stats(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> dict:
                                                                              
        if not self._db:
            return {
                "decisions": 0, "tasks": 0, "unassigned": 0,
                "risks": 0, "critical_risks": 0,
                "open_questions": 0, "dependencies": 0,
                "tasks_completed": 0,
            }

        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import (
            ActionItemORM,
            DecisionORM,
            OpenQuestionORM,
            RiskORM,
        )
        from app.domains.graph.infra.orm_models import TaskDependencyORM

                         
        r = await self._db.execute(
            select(func.count(DecisionORM.id)).where(
                DecisionORM.meeting_id == meeting_id,
                DecisionORM.org_id == org_id,
                DecisionORM.deleted_at.is_(None),
            )
        )
        decisions_count = r.scalar_one() or 0

                         
        r = await self._db.execute(
            select(ActionItemORM.status, ActionItemORM.owner_id, func.count(ActionItemORM.id))
            .where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
            .group_by(ActionItemORM.status, ActionItemORM.owner_id)
        )
        rows = r.fetchall()

        tasks_total     = 0
        tasks_completed = 0
        unassigned      = 0
        for status, owner_id, count in rows:
            tasks_total += count
            if status == "completed":
                tasks_completed += count
            if owner_id is None:
                unassigned += count

               
        r = await self._db.execute(
            select(RiskORM.severity, func.count(RiskORM.id)).where(
                RiskORM.meeting_id == meeting_id,
                RiskORM.org_id == org_id,
            ).group_by(RiskORM.severity)
        )
        risks_total = 0
        critical_risks = 0
        for severity, count in r.fetchall():
            risks_total += count
            if severity == "critical":
                critical_risks += count

                        
        r = await self._db.execute(
            select(func.count(OpenQuestionORM.id)).where(
                OpenQuestionORM.meeting_id == meeting_id,
                OpenQuestionORM.org_id == org_id,
            )
        )
        open_questions = r.scalar_one() or 0

                                                  
        r = await self._db.execute(
            select(func.count(TaskDependencyORM.id))
            .join(ActionItemORM, ActionItemORM.id == TaskDependencyORM.upstream_id)
            .where(
                ActionItemORM.meeting_id == meeting_id,
                TaskDependencyORM.org_id == org_id,
            )
        )
        dependencies = r.scalar_one() or 0

        return {
            "decisions":      decisions_count,
            "tasks":          tasks_total,
            "tasks_completed": tasks_completed,
            "unassigned":     unassigned,
            "risks":          risks_total,
            "critical_risks": critical_risks,
            "open_questions": open_questions,
            "dependencies":   dependencies,
        }

    def _build_analytics(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
        stats: dict,
    ) -> MeetingAnalytics:
        tasks = stats["tasks"]
        completed = stats["tasks_completed"]
        execution_rate = round((completed / tasks * 100), 2) if tasks > 0 else 0.0

        return MeetingAnalytics(
            id=uuid.uuid4(),
            org_id=org_id,
            meeting_id=meeting_id,
            decisions_count=stats["decisions"],
            action_items_count=tasks,
            unassigned_tasks=stats["unassigned"],
            risks_count=stats["risks"],
            critical_risks=stats["critical_risks"],
            dependencies_count=stats["dependencies"],
            open_questions_count=stats["open_questions"],
            execution_rate=execution_rate,
        )

    async def _refresh_execution_rate(
        self,
        existing: MeetingAnalytics,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics:
           
        if not self._db:
            return existing

        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import ActionItemORM

        r = await self._db.execute(
            select(func.count(ActionItemORM.id)).where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.status == "completed",
                ActionItemORM.deleted_at.is_(None),
            )
        )
        completed = r.scalar_one() or 0
        total = existing.action_items_count

        new_rate = round((completed / total * 100), 2) if total > 0 else 0.0
        if abs(new_rate - existing.execution_rate) < 0.1:
            return existing                                       

        existing.execution_rate = new_rate
        existing.updated_at = datetime.now(timezone.utc)
        return await self._repo.upsert(existing)
