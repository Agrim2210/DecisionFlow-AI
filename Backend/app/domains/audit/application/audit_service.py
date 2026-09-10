from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.domains.audit.application.queries import ListAuditLogsQuery
from app.domains.audit.domain.entities import AuditLog
from app.domains.audit.domain.exceptions import AuditLogNotFoundError
from app.domains.audit.domain.repositories import IAuditRepository

logger = structlog.get_logger(__name__)


class AuditService:

    def __init__(self, repo: IAuditRepository) -> None:
        self._repo = repo

    async def log(
        self,
        org_id: uuid.UUID,
        actor_id: uuid.UUID,
        actor_type: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        before_state: dict[str, Any] | None = None,
        after_state: dict[str, Any] | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=uuid.uuid4(),
            org_id=org_id,
            actor_id=actor_id,
            actor_type=actor_type,
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            before_state=before_state or {},
            after_state=after_state or {},
            ip_address=ip_address,
            metadata=metadata or {},
            occurred_at=datetime.now(timezone.utc),
        )
        try:
            result = await self._repo.append(entry)
            logger.debug(
                "audit_logged",
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=str(aggregate_id),
            )
            return result
        except Exception as exc:
            logger.error(
                "audit_write_failed",
                event_type=event_type,
                aggregate_id=str(aggregate_id),
                error=str(exc),
            )
            raise

    async def list_logs(self, query: ListAuditLogsQuery) -> list[AuditLog]:
        return await self._repo.list(
            org_id=query.org_id,
            limit=query.limit + 1,
            cursor_id=query.cursor_id,
            actor_id=query.actor_id,
            aggregate_type=query.aggregate_type,
            event_type=query.event_type,
            date_from=query.date_from,
            date_to=query.date_to,
        )

    async def get_log(self, log_id: uuid.UUID, org_id: uuid.UUID) -> AuditLog:
        log = await self._repo.get_by_id(log_id, org_id)
        if not log:
            raise AuditLogNotFoundError()
        return log
