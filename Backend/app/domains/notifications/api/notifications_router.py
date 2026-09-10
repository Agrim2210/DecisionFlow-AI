   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.notifications.api.schemas import (
    InboxResponse,
    NotificationResponse,
    UnreadCountResponse,
    map_notification,
)
from app.domains.notifications.application.commands import (
    MarkAllReadCommand,
    MarkNotificationReadCommand,
)
from app.domains.notifications.application.notification_service import NotificationService
from app.domains.notifications.application.queries import GetInboxQuery, GetUnreadCountQuery
from app.domains.notifications.infra.repositories import SQLNotificationRepository
from app.shared.deps import CurrentUser, DBSession
from app.shared.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _svc(db) -> NotificationService:
    return NotificationService(
        notif_repo=SQLNotificationRepository(db),
        email_adapter=None,
        slack_adapter=None,
    )


@router.get("", response_model=InboxResponse, summary="Get my notification inbox")
async def get_inbox(
    current_user: CurrentUser, db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    unread_only: bool = Query(default=False),
) -> InboxResponse:
    svc = _svc(db)
    cursor_id = None
    if cursor:
        try:
            cursor_id = decode_cursor(cursor)
        except ValueError:
            pass

    notifications = await svc.get_inbox(GetInboxQuery(
        recipient_id=current_user.id, org_id=current_user.org_id,
        limit=limit, cursor_id=cursor_id, unread_only=unread_only,
    ))
    unread_count = await svc.get_unread_count(GetUnreadCountQuery(
        recipient_id=current_user.id, org_id=current_user.org_id,
    ))

    has_next = len(notifications) > limit
    page = notifications[:limit]
    return InboxResponse(
        notifications=[map_notification(n) for n in page],
        unread_count=unread_count, has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


@router.get("/unread", response_model=UnreadCountResponse, summary="Get unread count for badge")
async def get_unread_count(current_user: CurrentUser, db: DBSession) -> UnreadCountResponse:
    svc = _svc(db)
    count = await svc.get_unread_count(GetUnreadCountQuery(
        recipient_id=current_user.id, org_id=current_user.org_id,
    ))
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification read")
async def mark_read(notification_id: uuid.UUID, current_user: CurrentUser, db: DBSession) -> NotificationResponse:
    svc = _svc(db)
    notif = await svc.mark_read(MarkNotificationReadCommand(
        notif_id=notification_id, org_id=current_user.org_id, user_id=current_user.id,
    ))
    return map_notification(notif)


@router.patch("/read-all", response_model=UnreadCountResponse, summary="Mark all notifications read")
async def mark_all_read(current_user: CurrentUser, db: DBSession) -> UnreadCountResponse:
    svc = _svc(db)
    await svc.mark_all_read(MarkAllReadCommand(org_id=current_user.org_id, user_id=current_user.id))
    return UnreadCountResponse(unread_count=0)
