   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.extraction.domain.entities import Decision
from app.domains.extraction.domain.repositories import IDecisionRepository
from app.domains.extraction.infra.orm_models import DecisionORM


                                                                     

def _to_entity(orm: DecisionORM) -> Decision:
    return Decision(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        title=orm.title,
        description=orm.description,
        decision_type=orm.decision_type,
        status=orm.status,
        confidence_score=float(orm.confidence_score),
        ai_raw_output=dict(orm.ai_raw_output or {}),
        made_by=list(orm.made_by or []),
        effective_date=orm.effective_date,
        review_date=orm.review_date,
        embedding=list(orm.embedding) if orm.embedding is not None else None,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )


                                                                      

class SQLDecisionRepository(IDecisionRepository):
       

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, decisions: list[Decision]) -> list[Decision]:
           
        orm_objects: list[DecisionORM] = []
        for d in decisions:
            orm = DecisionORM(
                id=d.id,
                org_id=d.org_id,
                meeting_id=d.meeting_id,
                title=d.title,
                description=d.description,
                decision_type=d.decision_type,
                status=d.status,
                confidence_score=d.confidence_score,
                ai_raw_output=d.ai_raw_output,
                made_by=d.made_by,
                effective_date=d.effective_date,
                review_date=d.review_date,
                embedding=d.embedding,
            )
            self._db.add(orm)
            orm_objects.append(orm)

        await self._db.flush()
        return [_to_entity(o) for o in orm_objects]

    async def get_by_id(
        self, decision_id: uuid.UUID, org_id: uuid.UUID
    ) -> Decision | None:
        result = await self._db.execute(
            select(DecisionORM).where(
                DecisionORM.id == decision_id,
                DecisionORM.org_id == org_id,                         
                DecisionORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _to_entity(orm) if orm else None

    async def list_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[Decision]:
        result = await self._db.execute(
            select(DecisionORM).where(
                DecisionORM.meeting_id == meeting_id,
                DecisionORM.org_id == org_id,
                DecisionORM.deleted_at.is_(None),
            ).order_by(DecisionORM.created_at.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        decision_type: str | None = None,
        status: str | None = None,
    ) -> list[Decision]:
        q = select(DecisionORM).where(
            DecisionORM.org_id == org_id,
            DecisionORM.deleted_at.is_(None),
        )
        if decision_type:
            q = q.where(DecisionORM.decision_type == decision_type)
        if status:
            q = q.where(DecisionORM.status == status)
        if cursor_id:
            q = q.where(DecisionORM.id > cursor_id)
        q = q.order_by(DecisionORM.created_at.desc()).limit(limit)
        result = await self._db.execute(q)
        return [_to_entity(r) for r in result.scalars().all()]

    async def update(self, decision: Decision) -> Decision:
        result = await self._db.execute(
            select(DecisionORM).where(DecisionORM.id == decision.id)
        )
        orm = result.scalar_one()
        orm.title = decision.title
        orm.description = decision.description
        orm.status = decision.status
        orm.effective_date = decision.effective_date
        orm.review_date = decision.review_date
        orm.deleted_at = decision.deleted_at
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        return _to_entity(orm)

    async def bulk_upsert_embeddings(
        self, items: list[tuple[uuid.UUID, list[float]]]
    ) -> None:
           
        for decision_id, embedding in items:
            await self._db.execute(
                update(DecisionORM)
                .where(DecisionORM.id == decision_id)
                .values(embedding=embedding)
            )
                                               
