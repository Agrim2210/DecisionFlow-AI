   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from app.domains.extraction.application.commands import UpdateRiskStatusCommand
from app.domains.extraction.application.queries import GetRiskQuery, ListRisksQuery
from app.domains.extraction.domain.entities import Risk, RiskStatus
from app.domains.extraction.domain.exceptions import RiskNotFoundError
from app.domains.extraction.domain.repositories import IRiskRepository

logger = structlog.get_logger(__name__)

                                   
_RISK_TRANSITIONS: dict[str, set[str]] = {
    "open":         {"acknowledged", "resolved", "dismissed"},
    "acknowledged": {"resolved", "dismissed"},
    "resolved":     set(),              
    "dismissed":    set(),              
}


class RiskService:

    def __init__(self, risk_repo: IRiskRepository) -> None:
        self._repo = risk_repo

    async def get(self, query: GetRiskQuery) -> Risk:
        risk = await self._repo.get_by_id(query.risk_id, query.org_id)
        if not risk:
            raise RiskNotFoundError()
        return risk

    async def list(self, query: ListRisksQuery) -> list[Risk]:
        if query.meeting_id:
            risks = await self._repo.list_by_meeting(query.meeting_id, query.org_id)
                                                                     
            if query.severity:
                risks = [r for r in risks if r.severity == query.severity]
            if query.status:
                risks = [r for r in risks if r.status == query.status]
            return risks

        return await self._repo.list_by_org(
            org_id=query.org_id,
            severity=query.severity,
            status=query.status,
            limit=query.limit,
        )

    async def update_status(self, cmd: UpdateRiskStatusCommand) -> Risk:
        risk = await self._repo.get_by_id(cmd.risk_id, cmd.org_id)
        if not risk:
            raise RiskNotFoundError()

        allowed = _RISK_TRANSITIONS.get(risk.status, set())
        if cmd.new_status not in allowed:
            from app.shared.exceptions import BadRequestError
            raise BadRequestError(
                f"Cannot transition risk from '{risk.status}' → '{cmd.new_status}'. "
                f"Allowed: {sorted(allowed) or 'none (terminal state)'}",
            )

        if cmd.new_status == "acknowledged":
            risk.acknowledge()
        elif cmd.new_status == "resolved":
            risk.resolve()
        elif cmd.new_status == "dismissed":
            risk.dismiss()

        updated = await self._repo.update(risk)

        logger.info(
            "risk_status_updated",
            risk_id=str(cmd.risk_id),
            new_status=cmd.new_status,
            by=str(cmd.updated_by),
        )
        return updated

    async def get_open_critical(self, org_id: uuid.UUID) -> list[Risk]:
                                                                       
        return await self._repo.list_by_org(
            org_id=org_id,
            severity="critical",
            status="open",
            limit=50,
        )

    async def get_summary_by_severity(self, org_id: uuid.UUID) -> dict[str, int]:
           
        all_open = await self._repo.list_by_org(org_id=org_id, status="open", limit=500)
        summary: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for risk in all_open:
            if risk.severity in summary:
                summary[risk.severity] += 1
        return summary
