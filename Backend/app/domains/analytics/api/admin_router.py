   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.analytics.api.schemas import (
    MeetingAnalyticsResponse,
    OrgDashboardResponse,
    ReliabilityListResponse,
    ReliabilityTrendResponse,
    map_meeting_analytics,
    map_org_dashboard,
    map_reliability_snapshot,
)
from app.domains.analytics.application.analytics_service import AnalyticsService
from app.domains.analytics.infra.repositories import (
    SQLMeetingAnalyticsRepository,
    SQLSnapshotRepository,
)
from app.shared.deps import AdminUser, CurrentUser, DBSession

router = APIRouter(prefix="/analytics", tags=["Analytics — Admin"])


def _svc(db) -> AnalyticsService:
    return AnalyticsService(
        snapshot_repo=SQLSnapshotRepository(db),
        meeting_analytics_repo=SQLMeetingAnalyticsRepository(db),
        db=db,
    )


                                                                    

@router.get(
    "/dashboard",
    response_model=OrgDashboardResponse,
    summary="[Admin] Org-wide execution dashboard",
    description=(
        "Aggregated KPIs for the entire organization:\n\n"
        "- Meeting and decision counts\n"
        "- Task breakdown by status (pending / in_progress / completed / overdue / blocked)\n"
        "- Unassigned task count (auto-flagged as risk)\n"
        "- Active escalation count\n"
        "- Average org reliability score\n"
        "- Org execution rate (completed / total * 100)\n"
        "- Top 5 performers and at-risk users (score < 70)\n\n"
        "Uses live DB aggregation + cached hourly reliability snapshots."
    ),
)
async def get_org_dashboard(
    current_user: AdminUser,
    db: DBSession,
) -> OrgDashboardResponse:
    svc = _svc(db)
    dashboard = await svc.get_org_dashboard(current_user.org_id)
    return map_org_dashboard(dashboard)


                                                                    

@router.get(
    "/reliability",
    response_model=ReliabilityListResponse,
    summary="[Admin] All users' reliability scores",
    description=(
        "Latest reliability snapshot for every active user in the org. "
        "Sorted by reliability_score descending (best performers first). "
        "Scores are recalculated hourly by the Celery Beat analytics task. "
        "Use this to power the reliability leaderboard in the admin panel."
    ),
)
async def get_all_reliability(
    current_user: AdminUser,
    db: DBSession,
) -> ReliabilityListResponse:
    svc = _svc(db)
    snapshots = await svc.get_all_user_reliability(current_user.org_id)
    avg = (
        round(sum(s.reliability_score for s in snapshots) / len(snapshots), 2)
        if snapshots else 0.0
    )
    return ReliabilityListResponse(
        snapshots=[map_reliability_snapshot(s) for s in snapshots],
        org_avg_score=avg,
        total_users=len(snapshots),
    )


                                                                   

@router.get(
    "/reliability/{user_id}",
    response_model=ReliabilityTrendResponse,
    summary="[Admin] 30-day reliability trend for a specific user",
    description=(
        "Returns up to 90 days of daily reliability snapshots for a user "
        "(oldest first) suitable for a trend line chart. "
        "Also returns trend_direction ('up' / 'down' / 'stable') "
        "and the numeric score change over the lookback period."
    ),
)
async def get_user_reliability_trend(
    user_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
    days: int = Query(
        default=30,
        ge=7,
        le=90,
        description="Lookback window in days (7–90)",
    ),
) -> ReliabilityTrendResponse:
    from app.domains.analytics.api.schemas import ReliabilityTrendResponse

    svc = _svc(db)
    snapshots = await svc.get_user_reliability(user_id, current_user.org_id, days)

    current_score = snapshots[-1].reliability_score if snapshots else 0.0
    first_score   = snapshots[0].reliability_score  if len(snapshots) > 1 else current_score

    if current_score > first_score + 2:
        trend_direction = "up"
    elif current_score < first_score - 2:
        trend_direction = "down"
    else:
        trend_direction = "stable"

    return ReliabilityTrendResponse(
        user_id=user_id,
        current_score=round(current_score, 2),
        trend=[map_reliability_snapshot(s) for s in snapshots],
        trend_direction=trend_direction,
        change_pct=round(current_score - first_score, 2),
    )


                                                                   

@router.get(
    "/meetings/{meeting_id}",
    response_model=MeetingAnalyticsResponse,
    summary="[Admin] Per-meeting extraction and execution metrics",
    description=(
        "Returns counts of all entities extracted from a meeting "
        "(decisions, tasks, risks, open questions, dependencies) "
        "plus the current execution rate for that meeting's tasks. "
        "Available to admin+ — see /analytics/me for worker-scoped stats."
    ),
)
async def get_meeting_analytics(
    meeting_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> MeetingAnalyticsResponse:
    svc = _svc(db)
    analytics = await svc.get_meeting_analytics(meeting_id, current_user.org_id)
    return map_meeting_analytics(analytics)
