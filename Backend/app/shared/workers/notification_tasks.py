from __future__ import annotations
import asyncio
import uuid
from typing import Any
from app.shared.workers.celery_app import celery_app
from app.shared.workers.async_runner import run_async


async def _send_notification_impl(
    org_id: str,
    recipient_id: str,
    event_type: str,
    channels: list[str],
    subject: str,
    body: str,
    payload: dict[str, Any],
    related_item_id: str | None = None,
    related_item_type: str | None = None,
) -> dict:
    from app.shared.database import get_db_context
    from app.domains.notifications.application.notification_service import NotificationService
    from app.domains.notifications.application.commands import SendNotificationCommand
    from app.domains.notifications.infra.repositories import SQLNotificationRepository
    from app.domains.notifications.infra.email_adapter import EmailAdapter
    from app.domains.notifications.infra.slack_adapter import SlackAdapter

    async with get_db_context() as db:
        svc = NotificationService(
            notif_repo=SQLNotificationRepository(db),
            email_adapter=EmailAdapter(),
            slack_adapter=SlackAdapter(),
        )
        created = await svc.send(SendNotificationCommand(
            org_id=uuid.UUID(org_id),
            recipient_id=uuid.UUID(recipient_id),
            event_type=event_type,
            channels=channels,
            subject=subject,
            body=body,
            payload=payload,
            related_item_id=uuid.UUID(related_item_id) if related_item_id else None,
            related_item_type=related_item_type,
        ))
    return {"sent": len(created)}


async def _dispatch_pipeline_notifications_impl(
    org_id: str,
    meeting_id: str,
    created_by: str,
    decisions_count: int,
    tasks_count: int,
    risks_count: int,
) -> dict:
    from app.shared.database import get_db_context
    from app.domains.notifications.application.notification_service import NotificationService
    from app.domains.notifications.application.commands import SendNotificationCommand
    from app.domains.notifications.infra.repositories import SQLNotificationRepository
    from app.domains.identity.infra.repositories import SQLUserRepository
    from app.domains.notifications.domain.entities import NotifChannel, NotifEventType
    from app.domains.notifications.infra.email_adapter import EmailAdapter

    async with get_db_context() as db:
        user = await SQLUserRepository(db).get_by_id(
            uuid.UUID(created_by), uuid.UUID(org_id)
        )
        if not user:
            raise ValueError("Meeting creator was not found in the organisation")

        svc = NotificationService(
            notif_repo=SQLNotificationRepository(db),
            email_adapter=EmailAdapter(),
            slack_adapter=None,
        )
        await svc.send(SendNotificationCommand(
            org_id=uuid.UUID(org_id),
            recipient_id=uuid.UUID(created_by),
            event_type=NotifEventType.MEETING_PROCESSED,
            channels=[NotifChannel.IN_APP, NotifChannel.EMAIL],
            subject="✅ Meeting Processed",
            body=(
                f"Your meeting has been processed.\n"
                f"Decisions: {decisions_count} | Tasks: {tasks_count} | Risks: {risks_count}"
            ),
            payload={
                "event_type": NotifEventType.MEETING_PROCESSED,
                "meeting_id": meeting_id,
                "meeting_title": "Meeting",
                "decision_count": decisions_count,
                "task_count": tasks_count,
                "risk_count": risks_count,
                "recipient_email": user.email,
                "recipient_name": user.name,
            },
            related_item_id=uuid.UUID(meeting_id),
            related_item_type="meeting",
        ))
    return {"ok": True}


async def _queue_pending_owner_welcome_emails_impl() -> dict:
                                                                                    
    from sqlalchemy import exists, select

    from app.shared.database import get_db_context
    from app.domains.identity.infra.orm_models import OrganizationORM, UserORM
    from app.domains.notifications.domain.entities import NotifChannel, NotifStatus
    from app.domains.notifications.infra.orm_models import NotificationORM

    async with get_db_context() as db:
        welcome_already_sent = exists().where(
            NotificationORM.recipient_id == UserORM.id,
            NotificationORM.event_type == "user_registered",
            NotificationORM.channel == NotifChannel.EMAIL,
            NotificationORM.status.in_([NotifStatus.SENT, NotifStatus.DELIVERED]),
        )
        result = await db.execute(
            select(UserORM, OrganizationORM)
            .join(OrganizationORM, OrganizationORM.id == UserORM.org_id)
            .where(
                UserORM.role == "owner",
                UserORM.is_active.is_(True),
                UserORM.deleted_at.is_(None),
                OrganizationORM.deleted_at.is_(None),
                ~welcome_already_sent,
            )
        )
        owners = result.all()

    for owner, organization in owners:
        send_notification.delay(
            org_id=str(organization.id),
            recipient_id=str(owner.id),
            event_type="user_registered",
            channels=[NotifChannel.EMAIL],
            subject="Welcome to DecisionFlow AI",
            body=(
                f"Hi {owner.name},\n\n"
                f"Your organization, {organization.name}, is ready. "
                "You are its owner and can now invite your team.\n\n"
                "— DecisionFlow AI"
            ),
            payload={
                "recipient_email": owner.email,
                "recipient_name": owner.name,
                "org_name": organization.name,
            },
        )
    return {"queued": len(owners)}


@celery_app.task(
    name="app.shared.workers.notification_tasks.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_notification(self, **kwargs):
    try:
        return run_async(_send_notification_impl(**kwargs))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.shared.workers.notification_tasks.dispatch_pipeline_notifications",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def dispatch_pipeline_notifications(self, **kwargs):
    try:
        return run_async(_dispatch_pipeline_notifications_impl(**kwargs))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.shared.workers.notification_tasks.queue_pending_owner_welcome_emails",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def queue_pending_owner_welcome_emails(self):
    try:
        return run_async(_queue_pending_owner_welcome_emails_impl())
    except Exception as exc:
        raise self.retry(exc=exc)
