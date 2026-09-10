from __future__ import annotations
import asyncio
from app.shared.workers.celery_app import celery_app
from app.shared.workers.async_runner import run_async


async def _refresh_reliability_impl() -> dict:
    from app.shared.database import get_db_context
    from sqlalchemy import select
    from app.domains.identity.infra.orm_models import OrganizationORM
    from app.domains.analytics.application.analytics_service import AnalyticsService
    from app.domains.analytics.infra.snapshot_repo import SQLSnapshotRepository
    from app.domains.analytics.infra.analytics_repo import SQLMeetingAnalyticsRepository

    total = 0
    async with get_db_context() as db:
        r = await db.execute(select(OrganizationORM.id).where(OrganizationORM.deleted_at.is_(None)))
        org_ids = [row[0] for row in r.fetchall()]
        for org_id in org_ids:
            try:
                svc = AnalyticsService(
                    snapshot_repo=SQLSnapshotRepository(db),
                    meeting_analytics_repo=SQLMeetingAnalyticsRepository(db),
                    db=db,
                )
                total += await svc.refresh_reliability_snapshots(org_id)
            except Exception:
                pass
    return {"users_refreshed": total}


async def _refresh_execution_rates_impl() -> dict:
    from app.shared.database import get_db_context
    from sqlalchemy import select
    from app.domains.identity.infra.orm_models import OrganizationORM
    from app.domains.analytics.application.analytics_service import AnalyticsService
    from app.domains.analytics.infra.snapshot_repo import SQLSnapshotRepository
    from app.domains.analytics.infra.analytics_repo import SQLMeetingAnalyticsRepository

    total = 0
    async with get_db_context() as db:
        r = await db.execute(select(OrganizationORM.id).where(OrganizationORM.deleted_at.is_(None)))
        org_ids = [row[0] for row in r.fetchall()]
        for org_id in org_ids:
            try:
                svc = AnalyticsService(
                    snapshot_repo=SQLSnapshotRepository(db),
                    meeting_analytics_repo=SQLMeetingAnalyticsRepository(db),
                    db=db,
                )
                total += await svc.refresh_meeting_execution_rates(org_id)
            except Exception:
                pass
    return {"meetings_updated": total}


@celery_app.task(name="app.shared.workers.analytics_tasks.refresh_all_reliability", bind=True, max_retries=3)
def refresh_all_reliability(self):
    return run_async(_refresh_reliability_impl())


@celery_app.task(name="app.shared.workers.analytics_tasks.refresh_execution_rates", bind=True, max_retries=3)
def refresh_execution_rates(self):
    return run_async(_refresh_execution_rates_impl())
