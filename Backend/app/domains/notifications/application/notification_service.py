   
from __future__ import annotations

import uuid
from typing import Any

import structlog

from app.domains.notifications.application.commands import (
    MarkAllReadCommand,
    MarkNotificationReadCommand,
    SendNotificationCommand,
)
from app.domains.notifications.application.queries import (
    GetInboxQuery,
    GetUnreadCountQuery,
)
from app.domains.notifications.domain.entities import (
    Notification,
    NotifChannel,
    NotifStatus,
)
from app.domains.notifications.domain.exceptions import NotificationNotFoundError
from app.domains.notifications.domain.repositories import INotificationRepository

logger = structlog.get_logger(__name__)


class NotificationService:

    def __init__(
        self,
        notif_repo: INotificationRepository,
        email_adapter: Any = None,
        slack_adapter: Any = None,
    ) -> None:
        self._repo = notif_repo
        self._email = email_adapter
        self._slack = slack_adapter

    async def send(self, cmd: SendNotificationCommand) -> list[Notification]:
        created: list[Notification] = []
        for channel in cmd.channels:
            notif = Notification(
                id=uuid.uuid4(),
                org_id=cmd.org_id,
                recipient_id=cmd.recipient_id,
                event_type=cmd.event_type,
                channel=channel,
                status=NotifStatus.PENDING,
                subject=cmd.subject,
                body=cmd.body,
                related_item_id=cmd.related_item_id,
                related_item_type=cmd.related_item_type,
                                                                             
                                                                             
                payload={**cmd.payload, "event_type": cmd.event_type},
            )
            notif = await self._repo.create(notif)
            created.append(notif)
            await self._dispatch(notif)
        return created

    async def _dispatch(self, notif: Notification) -> None:
        try:
            if notif.channel == NotifChannel.EMAIL:
                if self._email:
                    sent = await self._email.send(
                        recipient_id=notif.recipient_id,
                        subject=notif.subject,
                        body=notif.body,
                        payload=notif.payload,
                    )
                    if not sent:
                        raise RuntimeError("Email delivery failed")
                else:
                    return

            elif notif.channel == NotifChannel.SLACK:
                if self._slack:
                    sent = await self._slack.send(
                        subject=notif.subject,
                        body=notif.body,
                        payload=notif.payload,
                    )
                    if not sent:
                        raise RuntimeError("Slack delivery failed")
                else:
                    return

            elif notif.channel == NotifChannel.IN_APP:
                pass                              

            notif.mark_sent()
            await self._repo.update(notif)

        except Exception as exc:
            logger.warning(
                "notification_dispatch_failed",
                notif_id=str(notif.id),
                channel=notif.channel,
                error=str(exc),
            )
            notif.mark_failed(str(exc))
            await self._repo.update(notif)

    async def get_inbox(self, query: GetInboxQuery) -> list[Notification]:
        return await self._repo.list_inbox(
            recipient_id=query.recipient_id,
            org_id=query.org_id,
            limit=query.limit + 1,
            cursor_id=query.cursor_id,
            unread_only=query.unread_only,
        )

    async def get_unread_count(self, query: GetUnreadCountQuery) -> int:
        return await self._repo.count_unread(
            recipient_id=query.recipient_id,
            org_id=query.org_id,
        )

    async def mark_read(self, cmd: MarkNotificationReadCommand) -> Notification:
        notif = await self._repo.mark_read(cmd.notif_id, cmd.org_id)
        if not notif:
            raise NotificationNotFoundError()
        return notif

    async def mark_all_read(self, cmd: MarkAllReadCommand) -> int:
        return await self._repo.mark_all_read(
            recipient_id=cmd.user_id,
            org_id=cmd.org_id,
        )
