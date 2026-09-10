   
from __future__ import annotations

from fastapi import APIRouter, Query

from app.domains.analytics.api.schemas import (
    MeetingAnalyticsResponse,
    ReliabilityTrendResponse,
    WorkerDashboardResponse,
    map_meeting_analytics,
    map_reliability_snapshot,
    map_worker_dashboard,
)
from app.domains.analytics.application.analytics_service import AnalyticsService
from app.domains.analytics.infra.repositories import (
    SQLMeetingAnalyticsRepository,
    SQLSnapshotRepository,
)
from app.shared.deps import CurrentUser, DBSession

router = APIRouter(prefix="/analytics", tags=["Analytics — Worker"])


def _svc(db) -> AnalyticsService:
    return AnalyticsService(
        snapshot_repo=SQLSnapshotRepository(db),
        meeting_analytics_repo=SQLMeetingAnalyticsRepository(db),
        db=db,
    )


                                                                    

@router.get(
    "/me",
    response_model=WorkerDashboardResponse,
    summary="[Worker] My personal performance dashboard",
    description=(
        "Returns a complete personal performance snapshot for the current user:\n\n"
        "- Task breakdown: pending / in_progress / completed / overdue / blocked\n"
        "- My reliability score (tasks completed on time / tasks assigned × 100)\n"
        "- My completion rate (tasks completed / tasks assigned × 100)\n"
        "- Number of meetings I have uploaded\n"
        "- Upcoming deadlines in the next 7 days (configurable)\n\n"
        "Always scoped to the authenticated user — cannot view another user's data here."
    ),
)
async def get_my_dashboard(
    current_user: CurrentUser,
    db: DBSession,
    upcoming_days: int = Query(
        default=7,
        ge=1,
        le=30,
        description="How many days ahead to look for upcoming deadlines",
    ),
) -> WorkerDashboardResponse:
    svc = _svc(db)
    dashboard = await svc.get_worker_dashboard(
        user_id=current_user.id,
        org_id=current_user.org_id,
        upcoming_days=upcoming_days,
    )
    return map_worker_dashboard(dashboard)


                                                                   

@router.get(
    "/me/reliability",
    response_model=ReliabilityTrendResponse,
    summary="[Worker] My reliability trend over time",
    description=(
        "Returns my daily reliability snapshots for the last N days "
        "(oldest first) — suitable for rendering a personal trend chart. "
        "Includes trend_direction ('up' / 'down' / 'stable') and "
        "the numeric score change over the lookback period."
    ),
)
async def get_my_reliability_trend(
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(
        default=30,
        ge=7,
        le=90,
        description="Lookback window in days (7–90)",
    ),
) -> ReliabilityTrendResponse:
    svc = _svc(db)
    snapshots = await svc.get_user_reliability(
        user_id=current_user.id,
        org_id=current_user.org_id,
        days=days,
    )

    current_score = snapshots[-1].reliability_score if snapshots else 0.0
    first_score   = snapshots[0].reliability_score  if len(snapshots) > 1 else current_score

    if current_score > first_score + 2:
        trend_direction = "up"
    elif current_score < first_score - 2:
        trend_direction = "down"
    else:
        trend_direction = "stable"

    return ReliabilityTrendResponse(
        user_id=current_user.id,
        current_score=round(current_score, 2),
        trend=[map_reliability_snapshot(s) for s in snapshots],
        trend_direction=trend_direction,
        change_pct=round(current_score - first_score, 2),
    )


                                                                    

@router.get(
    "/me/upcoming",
    summary="[Worker] My upcoming task deadlines",
    description=(
        "Returns tasks assigned to me that are due within the next N days, "
        "sorted by due_date ascending (soonest first). "
        "Use this to populate the 'What's due soon?' widget on the worker panel."
    ),
)
async def get_my_upcoming_deadlines(
    current_user: CurrentUser,
    db: DBSession,
    days: int = Query(
        default=7,
        ge=1,
        le=30,
        description="Look-ahead window in days",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of tasks to return",
    ),
) -> list[dict]:
       
    from datetime import datetime, timedelta, timezone
    from sqlalchemy import select
    from app.domains.extraction.infra.orm_models import ActionItemORM

    cutoff = datetime.now(timezone.utc) + timedelta(days=days)

    result = await db.execute(
        select(
            ActionItemORM.id,
            ActionItemORM.title,
            ActionItemORM.due_date,
            ActionItemORM.priority,
            ActionItemORM.status,
        )
        .where(
            ActionItemORM.owner_id == current_user.id,
            ActionItemORM.org_id == current_user.org_id,
            ActionItemORM.due_date <= cutoff,
            ActionItemORM.due_date.isnot(None),
            ActionItemORM.status.notin_(["completed", "cancelled"]),
            ActionItemORM.deleted_at.is_(None),
        )
        .order_by(ActionItemORM.due_date.asc())
        .limit(limit)
    )

    rows = result.fetchall()
    return [
        {
            "task_id":  str(row.id),
            "title":    row.title,
            "due_date": row.due_date.isoformat() if row.due_date else None,
            "priority": row.priority,
            "status":   row.status,
        }
        for row in rows
    ]


                                                                    

@router.get(
    "/me/meetings",
    response_model=list[MeetingAnalyticsResponse],
    summary="[Worker] Analytics for meetings I uploaded",
    description=(
        "Returns extraction and execution metrics for meetings uploaded by me. "
        "Shows how many decisions, tasks, and risks came out of each of my meetings, "
        "and the current execution rate for those meeting's tasks."
    ),
)
async def get_my_meeting_analytics(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of meetings to return",
    ),
) -> list[MeetingAnalyticsResponse]:
    from sqlalchemy import select
    from app.domains.meetings.infra.orm_models import MeetingORM
    from app.domains.analytics.infra.orm_models import MeetingAnalyticsORM

                                            
    result = await db.execute(
        select(MeetingORM.id)
        .where(
            MeetingORM.created_by == current_user.id,
            MeetingORM.org_id == current_user.org_id,
            MeetingORM.deleted_at.is_(None),
        )
        .order_by(MeetingORM.created_at.desc())
        .limit(limit)
    )
    meeting_ids = [row[0] for row in result.fetchall()]

    if not meeting_ids:
        return []

                                       
    result = await db.execute(
        select(MeetingAnalyticsORM)
        .where(
            MeetingAnalyticsORM.meeting_id.in_(meeting_ids),
            MeetingAnalyticsORM.org_id == current_user.org_id,
        )
    )
    analytics_list = result.scalars().all()

                                              
    from app.domains.analytics.domain.entities import MeetingAnalytics
    import uuid as _uuid

    entities = []
    for orm in analytics_list:
        entities.append(MeetingAnalytics(
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
        ))

    return [map_meeting_analytics(e) for e in entities]
