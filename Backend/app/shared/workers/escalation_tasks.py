from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from app.shared.workers.celery_app import celery_app
from app.shared.workers.async_runner import run_async


async def _scan_overdue_impl() -> dict:
    from app.shared.database import get_db_context
    from app.domains.extraction.infra.task_repo import SQLActionItemRepository
    from app.domains.notifications.infra.repositories import (
        SQLEscalationRepository, SQLEscalationPolicyRepository, SQLNotificationRepository,
    )
    from app.domains.notifications.application.escalation_service import EscalationService
    from app.domains.notifications.application.commands import TriggerEscalationCommand
    from sqlalchemy import select
    from app.domains.identity.infra.orm_models import OrganizationORM

    triggered = 0
    now = datetime.now(timezone.utc)

    async with get_db_context() as db:
        r = await db.execute(select(OrganizationORM.id).where(OrganizationORM.deleted_at.is_(None)))
        org_ids = [row[0] for row in r.fetchall()]

        for org_id in org_ids:
            repo = SQLActionItemRepository(db)
            tasks = await repo.get_overdue(org_id=org_id, as_of=now)
            if not tasks:
                continue

            svc = EscalationService(
                escalation_repo=SQLEscalationRepository(db),
                policy_repo=SQLEscalationPolicyRepository(db),
                notif_repo=SQLNotificationRepository(db),
            )
            for task in tasks:
                try:
                    task.mark_overdue()
                    await repo.update(task)
                    await svc.trigger(TriggerEscalationCommand(
                        org_id=org_id,
                        action_item_id=task.id,
                        action_item_title=task.title,
                        owner_id=task.owner_id,
                        due_date_str=task.due_date.strftime("%Y-%m-%d") if task.due_date else "unknown",
                    ))
                    triggered += 1
                except Exception:
                    pass
    return {"triggered": triggered}


async def _advance_escalations_impl() -> dict:
    from app.shared.database import get_db_context
    from app.domains.notifications.infra.repositories import (
        SQLEscalationRepository, SQLEscalationPolicyRepository, SQLNotificationRepository,
    )
    from app.domains.notifications.application.escalation_service import EscalationService
    from app.domains.notifications.application.commands import AdvanceEscalationCommand

    advanced = 0
    now = datetime.now(timezone.utc)

    async with get_db_context() as db:
        esc_repo = SQLEscalationRepository(db)
        due = await esc_repo.get_due_for_advancement(now)
        svc = EscalationService(
            escalation_repo=esc_repo,
            policy_repo=SQLEscalationPolicyRepository(db),
            notif_repo=SQLNotificationRepository(db),
        )
        for esc in due:
            try:
                await svc.advance(AdvanceEscalationCommand(
                    escalation_id=esc.id, org_id=esc.org_id,
                ))
                advanced += 1
            except Exception:
                pass
    return {"advanced": advanced}


@celery_app.task(name="app.shared.workers.escalation_tasks.scan_overdue_tasks", bind=True, max_retries=3)
def scan_overdue_tasks(self):
    return run_async(_scan_overdue_impl())


@celery_app.task(name="app.shared.workers.escalation_tasks.advance_escalations", bind=True, max_retries=3)
def advance_escalations(self):
    return run_async(_advance_escalations_impl())
