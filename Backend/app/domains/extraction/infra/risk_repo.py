   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.extraction.domain.entities import Risk
from app.domains.extraction.domain.repositories import IRiskRepository
from app.domains.extraction.infra.orm_models import RiskORM


                                                                     

def _to_entity(orm: RiskORM) -> Risk:
    return Risk(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        related_item_id=orm.related_item_id,
        related_item_type=orm.related_item_type,
        risk_type=orm.risk_type,
        severity=orm.severity,
        description=orm.description,
        recommendation=orm.recommendation,
        status=orm.status,
        resolved_at=orm.resolved_at,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


                                                                     

_SEVERITY_ORDER = case(
    (RiskORM.severity == "critical", 1),
    (RiskORM.severity == "high",     2),
    (RiskORM.severity == "medium",   3),
    (RiskORM.severity == "low",      4),
    else_=5,
)


                                                                      

class SQLRiskRepository(IRiskRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, risks: list[Risk]) -> list[Risk]:
           
        orm_objects: list[RiskORM] = []
        for r in risks:
            orm = RiskORM(
                id=r.id,
                org_id=r.org_id,
                meeting_id=r.meeting_id,
                related_item_id=r.related_item_id,
                related_item_type=r.related_item_type,
                risk_type=r.risk_type,
                severity=r.severity,
                description=r.description,
                recommendation=r.recommendation,
                status=r.status,
            )
            self._db.add(orm)
            orm_objects.append(orm)

        await self._db.flush()
        return [_to_entity(o) for o in orm_objects]

    async def get_by_id(
        self, risk_id: uuid.UUID, org_id: uuid.UUID
    ) -> Risk | None:
        result = await self._db.execute(
            select(RiskORM).where(
                RiskORM.id == risk_id,
                RiskORM.org_id == org_id,                   
            )
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[Risk]:
           
        result = await self._db.execute(
            select(RiskORM).where(
                RiskORM.meeting_id == meeting_id,
                RiskORM.org_id == org_id,
            ).order_by(_SEVERITY_ORDER, RiskORM.created_at.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Risk]:
           
        q = select(RiskORM).where(RiskORM.org_id == org_id)

        if severity:
            q = q.where(RiskORM.severity == severity)
        if status:
            q = q.where(RiskORM.status == status)

        q = q.order_by(_SEVERITY_ORDER, RiskORM.created_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_by_related_item(
        self, related_item_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[Risk]:
           
        result = await self._db.execute(
            select(RiskORM).where(
                RiskORM.related_item_id == related_item_id,
                RiskORM.org_id == org_id,
            ).order_by(_SEVERITY_ORDER)
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def update(self, risk: Risk) -> Risk:
           
        result = await self._db.execute(
            select(RiskORM).where(RiskORM.id == risk.id)
        )
        orm = result.scalar_one()
        orm.status = risk.status
        orm.resolved_at = risk.resolved_at
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return _to_entity(orm)

    async def count_open_by_severity(self, org_id: uuid.UUID) -> dict[str, int]:
           
        from sqlalchemy import func
        result = await self._db.execute(
            select(RiskORM.severity, func.count(RiskORM.id))
            .where(
                RiskORM.org_id == org_id,
                RiskORM.status == "open",
            )
            .group_by(RiskORM.severity)
        )
        summary: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for severity, count in result.fetchall():
            if severity in summary:
                summary[severity] = count
        return summary
