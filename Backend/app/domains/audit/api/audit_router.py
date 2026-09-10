from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.audit.api.schemas import AuditListResponse, AuditLogResponse, map_audit_log
from app.domains.audit.application.audit_service import AuditService
from app.domains.audit.application.queries import ListAuditLogsQuery
from app.domains.audit.infra.repositories import SQLAuditRepository
from app.shared.deps import AdminUser, DBSession
from app.shared.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


def _svc(db) -> AuditService:
    return AuditService(repo=SQLAuditRepository(db))


@router.get(
    "",
    response_model=AuditListResponse,
    summary="[Admin] List audit logs",
)
async def list_audit_logs(
    current_user: AdminUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    actor_id: uuid.UUID | None = Query(default=None),
    aggregate_type: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
) -> AuditListResponse:
    cursor_id = None
    if cursor:
        try:
            cursor_id = decode_cursor(cursor)
        except ValueError:
            pass

    svc = _svc(db)
    logs = await svc.list_logs(ListAuditLogsQuery(
        org_id=current_user.org_id,
        limit=limit,
        cursor_id=cursor_id,
        actor_id=actor_id,
        aggregate_type=aggregate_type,
        event_type=event_type,
    ))

    has_next = len(logs) > limit
    page = logs[:limit]

    return AuditListResponse(
        logs=[map_audit_log(l) for l in page],
        has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


@router.get(
    "/{log_id}",
    response_model=AuditLogResponse,
    summary="[Admin] Get a specific audit log entry",
)
async def get_audit_log(
    log_id: uuid.UUID,
    current_user: AdminUser,
    db: DBSession,
) -> AuditLogResponse:
    svc = _svc(db)
    log = await svc.get_log(log_id, current_user.org_id)
    return map_audit_log(log)
