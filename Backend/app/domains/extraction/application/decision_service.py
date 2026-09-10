   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from app.domains.extraction.application.commands import UpdateDecisionCommand
from app.domains.extraction.application.queries import GetDecisionQuery, ListDecisionsQuery
from app.domains.extraction.domain.entities import Decision, DecisionStatus
from app.domains.extraction.domain.exceptions import DecisionNotFoundError
from app.domains.extraction.domain.repositories import IDecisionRepository

logger = structlog.get_logger(__name__)


class DecisionService:

    def __init__(self, decision_repo: IDecisionRepository) -> None:
        self._repo = decision_repo

    async def get(self, query: GetDecisionQuery) -> Decision:
        d = await self._repo.get_by_id(query.decision_id, query.org_id)
        if not d:
            raise DecisionNotFoundError()
        return d

    async def list(self, query: ListDecisionsQuery) -> list[Decision]:
        if query.meeting_id:
            return await self._repo.list_by_meeting(query.meeting_id, query.org_id)
        return await self._repo.list_by_org(
            org_id=query.org_id,
            limit=query.limit + 1,
            cursor_id=query.cursor_id,
            decision_type=query.decision_type,
            status=query.status,
        )

    async def update(self, cmd: UpdateDecisionCommand) -> Decision:
        decision = await self._repo.get_by_id(cmd.decision_id, cmd.org_id)
        if not decision:
            raise DecisionNotFoundError()

        changed = False
        if cmd.title is not None and cmd.title != decision.title:
            decision.title = cmd.title
            changed = True
        if cmd.description is not None and cmd.description != decision.description:
            decision.description = cmd.description
            changed = True
        if cmd.status is not None and cmd.status != decision.status:
            decision.status = cmd.status
            changed = True

        if not changed:
            return decision

        decision.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(decision)

        logger.info(
            "decision_updated",
            decision_id=str(cmd.decision_id),
            org_id=str(cmd.org_id),
            by=str(cmd.updated_by),
            status=cmd.status,
        )
        return updated

    async def supersede(
        self,
        old_decision_id: uuid.UUID,
        org_id: uuid.UUID,
        superseded_by: uuid.UUID,
    ) -> Decision:
                                                                
        decision = await self._repo.get_by_id(old_decision_id, org_id)
        if not decision:
            raise DecisionNotFoundError()

        decision.supersede()
        updated = await self._repo.update(decision)
        logger.info("decision_superseded", old_id=str(old_decision_id), by=str(superseded_by))
        return updated
