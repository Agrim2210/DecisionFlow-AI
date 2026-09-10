   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.domains.extraction.domain.entities import ActionItem
from app.domains.extraction.domain.repositories import IActionItemRepository
from app.domains.extraction.infra.orm_models import ActionItemORM
from app.domains.identity.infra.orm_models import UserORM


                                                                     

def _to_entity(orm: ActionItemORM, owner_name: str | None = None) -> ActionItem:
    return ActionItem(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        decision_id=orm.decision_id,
        title=orm.title,
        description=orm.description,
        owner_id=orm.owner_id,
        owner_name=owner_name,
        status=orm.status,
        priority=orm.priority,
        due_date=orm.due_date,
        completed_at=orm.completed_at,
        confidence_score=float(orm.confidence_score),
        ai_raw_output=dict(orm.ai_raw_output or {}),
        embedding=list(orm.embedding) if orm.embedding is not None else None,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )


                                                                      

class SQLActionItemRepository(IActionItemRepository):

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, items: list[ActionItem]) -> list[ActionItem]:
        orm_objects: list[ActionItemORM] = []
        for t in items:
            orm = ActionItemORM(
                id=t.id,
                org_id=t.org_id,
                meeting_id=t.meeting_id,
                decision_id=t.decision_id,
                title=t.title,
                description=t.description,
                owner_id=t.owner_id,
                status=t.status,
                priority=t.priority,
                due_date=t.due_date,
                confidence_score=t.confidence_score,
                ai_raw_output=t.ai_raw_output,
                embedding=t.embedding,
            )
            self._db.add(orm)
            orm_objects.append(orm)
        await self._db.flush()
        return [_to_entity(o) for o in orm_objects]

    async def get_by_id(
        self, item_id: uuid.UUID, org_id: uuid.UUID
    ) -> ActionItem | None:
        OwnerUser = aliased(UserORM)
        result = await self._db.execute(
            select(ActionItemORM, OwnerUser.name.label("owner_name"))
            .outerjoin(OwnerUser, ActionItemORM.owner_id == OwnerUser.id)
            .where(
                ActionItemORM.id == item_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
        )
        row = result.one_or_none()
        if not row:
            return None
        return _to_entity(row[0], owner_name=row[1])

    async def list_by_meeting(
        self, meeting_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[ActionItem]:
        OwnerUser = aliased(UserORM)
        result = await self._db.execute(
            select(ActionItemORM, OwnerUser.name.label("owner_name"))
            .outerjoin(OwnerUser, ActionItemORM.owner_id == OwnerUser.id)
            .where(
                ActionItemORM.meeting_id == meeting_id,
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            ).order_by(ActionItemORM.created_at.asc())
        )
        return [_to_entity(row[0], owner_name=row[1]) for row in result.all()]

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        owner_id: uuid.UUID | None = None,
        status: str | None = None,
        overdue_only: bool = False,
    ) -> list[ActionItem]:
           
        OwnerUser = aliased(UserORM)
        q = (
            select(ActionItemORM, OwnerUser.name.label("owner_name"))
            .outerjoin(OwnerUser, ActionItemORM.owner_id == OwnerUser.id)
            .where(
                ActionItemORM.org_id == org_id,
                ActionItemORM.deleted_at.is_(None),
            )
        )
        if owner_id is not None:
            q = q.where(ActionItemORM.owner_id == owner_id)
        if status:
            q = q.where(ActionItemORM.status == status)
        if overdue_only:
            q = q.where(
                ActionItemORM.due_date < datetime.now(timezone.utc),
                ActionItemORM.status.notin_(["completed", "cancelled"]),
            )
        if cursor_id:
            q = q.where(ActionItemORM.id > cursor_id)
                                                                 
        q = q.order_by(ActionItemORM.due_date.asc().nullslast()).limit(limit)
        result = await self._db.execute(q)
        return [_to_entity(row[0], owner_name=row[1]) for row in result.all()]

    async def update(self, item: ActionItem) -> ActionItem:
        result = await self._db.execute(
            select(ActionItemORM).where(ActionItemORM.id == item.id)
        )
        orm = result.scalar_one()
        orm.title = item.title
        orm.description = item.description
        orm.owner_id = item.owner_id
        orm.status = item.status
        orm.priority = item.priority
        orm.due_date = item.due_date
        orm.completed_at = item.completed_at
        orm.deleted_at = item.deleted_at
        orm.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        owner_name = item.owner_name
        if orm.owner_id and not owner_name:
            user_res = await self._db.execute(
                select(UserORM.name).where(UserORM.id == orm.owner_id)
            )
            owner_name = user_res.scalar_one_or_none()
        elif not orm.owner_id:
            owner_name = None
        return _to_entity(orm, owner_name=owner_name)

    async def get_overdue(
        self, org_id: uuid.UUID, as_of: datetime
    ) -> list[ActionItem]:
           
        result = await self._db.execute(
            select(ActionItemORM).where(
                ActionItemORM.org_id == org_id,
                ActionItemORM.due_date < as_of,
                ActionItemORM.status.notin_(["completed", "cancelled"]),
                ActionItemORM.deleted_at.is_(None),
            ).order_by(ActionItemORM.due_date.asc())
        )
        return [_to_entity(r) for r in result.scalars().all()]

    async def bulk_upsert_embeddings(
        self, items: list[tuple[uuid.UUID, list[float]]]
    ) -> None:
                                                                  
        for item_id, embedding in items:
            await self._db.execute(
                update(ActionItemORM)
                .where(ActionItemORM.id == item_id)
                .values(embedding=embedding)
            )
