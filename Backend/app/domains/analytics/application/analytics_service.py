   
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.domains.analytics.domain.entities import (
    MeetingAnalytics,
    OrgDashboard,
    UserReliabilitySnapshot,
    WorkerDashboard,
)
from app.domains.analytics.domain.exceptions import MeetingAnalyticsNotFoundError
from app.domains.analytics.domain.repositories import (
    IMeetingAnalyticsRepository,
    ISnapshotRepository,
)
from app.domains.analytics.domain.value_objects import (
    ExecutionRate,
    ReliabilityScore,
)

logger = structlog.get_logger(__name__)


class AnalyticsService:

    def __init__(
        self,
        snapshot_repo: ISnapshotRepository,
        meeting_analytics_repo: IMeetingAnalyticsRepository,
        db: Any = None,                                                                 
    ) -> None:
        self._snapshots = snapshot_repo
        self._meeting_analytics = meeting_analytics_repo
        self._db = db

                                                                    
                                  
                                                                    

    async def get_org_dashboard(self, org_id: uuid.UUID) -> OrgDashboard:
           
        dashboard = OrgDashboard(org_id=org_id)

        if self._db is not None:
            await self._fill_org_counts(dashboard, org_id)

                                                              
        snapshots = await self._snapshots.list_by_org(org_id, limit=200)

        if snapshots:
            dashboard.avg_reliability_score = round(
                sum(s.reliability_score for s in snapshots) / len(snapshots), 2
            )
            dashboard.top_performers = [
                {"user_id": str(s.user_id), "score": s.reliability_score}
                for s in sorted(snapshots, key=lambda x: x.reliability_score, reverse=True)[:5]
            ]
            dashboard.at_risk_users = [
                {"user_id": str(s.user_id), "score": s.reliability_score}
                for s in sorted(snapshots, key=lambda x: x.reliability_score)[:5]
                if s.reliability_score < 70.0
            ]

        dashboard.org_execution_rate = dashboard.compute_execution_rate()
        return dashboard

    async def _fill_org_counts(self, dashboard: OrgDashboard, org_id: uuid.UUID) -> None:
                                                                     
        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import ActionItemORM, DecisionORM
        from app.domains.meetings.infra.orm_models import MeetingORM
        from app.domains.notifications.infra.orm_models import EscalationORM

                        
        r = await self._db.execute(
            select(func.count(MeetingORM.id)).where(
                MeetingORM.org_id == org_id,
                MeetingORM.deleted_at.is_(None),
            )
        )
        dashboard.total_meetings = r.scalar_one() or 0

                         
        r = await self._db.execute(
            select(func.count(DecisionORM.id)).where(
                DecisionORM.org_id == org_id,
                DecisionORM.deleted_at.is_(None),
            )
        )
        dashboard.total_decisions = r.scalar_one() or 0

                                                               
        r = await self._db.execute(
            select(ActionItemORM.status, func.count(ActionItemORM.id))
            .where(
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
            .group_by(ActionItemORM.status)
        )
        for status, count in r.fetchall():
            dashboard.total_tasks += count
            if status == "pending":
                dashboard.pending_tasks = count
            elif status == "in_progress":
                dashboard.in_progress_tasks = count
            elif status == "completed":
                dashboard.completed_tasks = count
            elif status == "overdue":
                dashboard.overdue_tasks = count
            elif status == "blocked":
                dashboard.blocked_tasks = count

                                                   
        r = await self._db.execute(
            select(func.count(ActionItemORM.id)).where(
                ActionItemORM.org_id == org_id,
                ActionItemORM.owner_id.is_(None),
                ActionItemORM.deleted_at.is_(None),
                ActionItemORM.status.notin_(["completed", "cancelled"]),
            )
        )
        dashboard.unassigned_tasks = r.scalar_one() or 0

                            
        r = await self._db.execute(
            select(func.count(EscalationORM.id)).where(
                EscalationORM.org_id == org_id,
                EscalationORM.status == "active",
            )
        )
        dashboard.active_escalations = r.scalar_one() or 0

                                                                    
                                      
                                                                    

    async def get_worker_dashboard(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        upcoming_days: int = 7,
    ) -> WorkerDashboard:
           
        dashboard = WorkerDashboard(user_id=user_id, org_id=org_id)

        if self._db is not None:
            await self._fill_worker_counts(dashboard, user_id, org_id, upcoming_days)

                                          
        snap = await self._snapshots.get_latest(user_id, org_id)
        if snap:
            dashboard.my_reliability_score = snap.reliability_score

        return dashboard

    async def _fill_worker_counts(
        self,
        dashboard: WorkerDashboard,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        upcoming_days: int,
    ) -> None:
        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import ActionItemORM
        from app.domains.meetings.infra.orm_models import MeetingORM

                                                   
        r = await self._db.execute(
            select(ActionItemORM.status, func.count(ActionItemORM.id))
            .where(
                ActionItemORM.owner_id == user_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
            .group_by(ActionItemORM.status)
        )
        for status, count in r.fetchall():
            dashboard.my_tasks_total += count
            if status == "pending":
                dashboard.my_tasks_pending = count
            elif status == "in_progress":
                dashboard.my_tasks_in_progress = count
            elif status == "completed":
                dashboard.my_tasks_completed = count
            elif status == "overdue":
                dashboard.my_tasks_overdue = count
            elif status == "blocked":
                dashboard.my_tasks_blocked = count

                           
        r = await self._db.execute(
            select(func.count(MeetingORM.id)).where(
                MeetingORM.created_by == user_id,
                MeetingORM.org_id == org_id,
                MeetingORM.deleted_at.is_(None),
            )
        )
        dashboard.my_meetings_count = r.scalar_one() or 0

                            
        cutoff = datetime.now(timezone.utc) + timedelta(days=upcoming_days)
        r = await self._db.execute(
            select(
                ActionItemORM.id,
                ActionItemORM.title,
                ActionItemORM.due_date,
                ActionItemORM.priority,
                ActionItemORM.status,
            )
            .where(
                ActionItemORM.owner_id == user_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.due_date <= cutoff,
                ActionItemORM.due_date.isnot(None),
                ActionItemORM.status.notin_(["completed", "cancelled"]),
                ActionItemORM.deleted_at.is_(None),
            )
            .order_by(ActionItemORM.due_date.asc())
            .limit(10)
        )
        dashboard.upcoming_deadlines = [
            {
                "task_id":  str(row.id),
                "title":    row.title,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "priority": row.priority,
                "status":   row.status,
            }
            for row in r.fetchall()
        ]

                                                                    
                                
                                                                    

    async def get_user_reliability(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> list[UserReliabilitySnapshot]:
                                                                    
        return await self._snapshots.get_trend(user_id, org_id, days)

    async def get_all_user_reliability(
        self, org_id: uuid.UUID
    ) -> list[UserReliabilitySnapshot]:
                                                                     
        return await self._snapshots.list_by_org(org_id)

                                                                    
                       
                                                                    

    async def get_meeting_analytics(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics:
           
        analytics = await self._meeting_analytics.get_by_meeting(meeting_id, org_id)
        if not analytics:
            raise MeetingAnalyticsNotFoundError(
                f"No analytics found for meeting {meeting_id}. "
                "Ensure the pipeline has completed."
            )
        return analytics

    async def compute_meeting_analytics(
        self,
        meeting_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> MeetingAnalytics:
           
        if self._db is None:
            raise RuntimeError("DB session required for compute_meeting_analytics")

        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import (
            ActionItemORM, DecisionORM, OpenQuestionORM, RiskORM,
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
            select(func.count(ActionItemORM.id)).where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
        )
        action_items_count = r.scalar_one() or 0

        r = await self._db.execute(
            select(func.count(ActionItemORM.id)).where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.owner_id.is_(None),
                ActionItemORM.deleted_at.is_(None),
            )
        )
        unassigned_tasks = r.scalar_one() or 0

                                                    
        r = await self._db.execute(
            select(func.count(ActionItemORM.id)).where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.status == "completed",
                ActionItemORM.deleted_at.is_(None),
            )
        )
        completed_tasks = r.scalar_one() or 0

                     
        r = await self._db.execute(
            select(func.count(RiskORM.id)).where(
                RiskORM.meeting_id == meeting_id,
                RiskORM.org_id == org_id,
            )
        )
        risks_count = r.scalar_one() or 0

        r = await self._db.execute(
            select(func.count(RiskORM.id)).where(
                RiskORM.meeting_id == meeting_id,
                RiskORM.org_id == org_id,
                RiskORM.severity == "critical",
            )
        )
        critical_risks = r.scalar_one() or 0

                              
        r = await self._db.execute(
            select(func.count(OpenQuestionORM.id)).where(
                OpenQuestionORM.meeting_id == meeting_id,
                OpenQuestionORM.org_id == org_id,
            )
        )
        open_questions_count = r.scalar_one() or 0

                                               
        try:
            from app.domains.extraction.infra.orm_models import ActionItemORM as AI
            r = await self._db.execute(
                select(func.count(TaskDependencyORM.id))
                .join(AI, AI.id == TaskDependencyORM.upstream_id)
                .where(
                    AI.meeting_id == meeting_id,
                    TaskDependencyORM.org_id == org_id,
                )
            )
            dependencies_count = r.scalar_one() or 0
        except Exception:
            dependencies_count = 0

                        
        exec_rate = ExecutionRate.compute(completed_tasks, action_items_count)

        analytics = MeetingAnalytics(
            id=uuid.uuid4(),
            org_id=org_id,
            meeting_id=meeting_id,
            decisions_count=decisions_count,
            action_items_count=action_items_count,
            unassigned_tasks=unassigned_tasks,
            risks_count=risks_count,
            critical_risks=critical_risks,
            dependencies_count=dependencies_count,
            open_questions_count=open_questions_count,
            execution_rate=float(exec_rate),
        )

        result = await self._meeting_analytics.upsert(analytics)

        logger.info(
            "meeting_analytics_computed",
            meeting_id=str(meeting_id),
            org_id=str(org_id),
            decisions=decisions_count,
            tasks=action_items_count,
            risks=risks_count,
            exec_rate=float(exec_rate),
        )
        return result

                                                                    
                                             
                                                                    

    async def refresh_reliability_snapshots(self, org_id: uuid.UUID) -> int:
           
        if self._db is None:
            return 0

        from sqlalchemy import select, update
        from app.domains.extraction.infra.orm_models import ActionItemORM
        from app.domains.identity.infra.orm_models import UserORM

                                      
        r = await self._db.execute(
            select(UserORM.id).where(
                UserORM.org_id == org_id,
                UserORM.is_active.is_(True),
                UserORM.deleted_at.is_(None),
            )
        )
        user_ids = [row[0] for row in r.fetchall()]

        snapshots: list[UserReliabilitySnapshot] = []
        now = datetime.now(timezone.utc)

        for user_id in user_ids:
                                          
            r = await self._db.execute(
                select(
                    ActionItemORM.status,
                    ActionItemORM.due_date,
                    ActionItemORM.completed_at,
                )
                .where(
                    ActionItemORM.owner_id == user_id,
                    ActionItemORM.org_id == org_id,
                    ActionItemORM.deleted_at.is_(None),
                )
            )
            tasks = r.fetchall()

            assigned   = len(tasks)
            completed  = sum(1 for t in tasks if t.status == "completed")
            cancelled  = sum(1 for t in tasks if t.status == "cancelled")
            overdue    = sum(1 for t in tasks if t.status == "overdue")

                                                                              
            on_time = sum(
                1 for t in tasks
                if t.status == "completed" and (
                    t.due_date is None or (
                        t.completed_at is not None and t.completed_at <= t.due_date
                    )
                )
            )

            score = ReliabilityScore.compute(on_time, assigned)

            snap = UserReliabilitySnapshot(
                id=uuid.uuid4(),
                org_id=org_id,
                user_id=user_id,
                snapshot_date=now,
                tasks_assigned=assigned,
                tasks_completed=completed,
                tasks_on_time=on_time,
                tasks_overdue=overdue,
                tasks_cancelled=cancelled,
                reliability_score=float(score),
            )
            snapshots.append(snap)

                                                                     
            await self._db.execute(
                update(UserORM)
                .where(UserORM.id == user_id)
                .values(reliability_score=float(score))
            )

                                                    
        upserted = await self._snapshots.bulk_upsert(snapshots)

        logger.info(
            "reliability_refreshed",
            org_id=str(org_id),
            users=len(user_ids),
            snapshots_upserted=upserted,
        )
        return upserted

    async def refresh_meeting_execution_rates(self, org_id: uuid.UUID) -> int:
           
        if self._db is None:
            return 0

        from sqlalchemy import func, select
        from app.domains.extraction.infra.orm_models import ActionItemORM

                                         
        existing = await self._meeting_analytics.list_by_org(org_id, limit=1000)
        updated = 0

        for analytics in existing:
                                                            
            r = await self._db.execute(
                select(
                    ActionItemORM.status,
                    func.count(ActionItemORM.id),
                )
                .where(
                    ActionItemORM.meeting_id == analytics.meeting_id,
                    ActionItemORM.org_id == org_id,
                    ActionItemORM.deleted_at.is_(None),
                )
                .group_by(ActionItemORM.status)
            )
            status_counts = {row[0]: row[1] for row in r.fetchall()}

            total     = sum(status_counts.values())
            completed = status_counts.get("completed", 0)

            new_rate = float(ExecutionRate.compute(completed, total))

            if abs(new_rate - analytics.execution_rate) > 0.01:
                await self._meeting_analytics.update_execution_rate(
                    meeting_id=analytics.meeting_id,
                    org_id=org_id,
                    execution_rate=new_rate,
                )
                updated += 1

        if updated:
            logger.info(
                "meeting_execution_rates_refreshed",
                org_id=str(org_id),
                meetings_updated=updated,
            )
        return updated
