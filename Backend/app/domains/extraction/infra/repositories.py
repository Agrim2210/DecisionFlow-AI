                                                                                
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.extraction.domain.entities import OpenQuestion
from app.domains.extraction.domain.repositories import IOpenQuestionRepository
from app.domains.extraction.infra.decision_repo import SQLDecisionRepository
from app.domains.extraction.infra.memory_repo import SQLMemoryRepository
from app.domains.extraction.infra.orm_models import OpenQuestionORM
from app.domains.extraction.infra.risk_repo import SQLRiskRepository
from app.domains.extraction.infra.task_repo import SQLActionItemRepository


def _to_entity(orm: OpenQuestionORM) -> OpenQuestion:
    return OpenQuestion(
        id=orm.id,
        org_id=orm.org_id,
        meeting_id=orm.meeting_id,
        question=orm.question,
        context=orm.context,
        status=orm.status,
        answer=orm.answer,
        answered_by=orm.answered_by,
        answered_at=orm.answered_at,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


class SQLOpenQuestionRepository(IOpenQuestionRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def bulk_create(self, questions: list[OpenQuestion]) -> list[OpenQuestion]:
        records = [
            OpenQuestionORM(
                id=question.id,
                org_id=question.org_id,
                meeting_id=question.meeting_id,
                question=question.question,
                context=question.context,
                status=question.status,
                answer=question.answer,
                answered_by=question.answered_by,
                answered_at=question.answered_at,
            )
            for question in questions
        ]
        self._db.add_all(records)
        await self._db.flush()
        return [_to_entity(record) for record in records]

    async def get_by_id(self, qid: uuid.UUID, org_id: uuid.UUID) -> OpenQuestion | None:
        result = await self._db.execute(
            select(OpenQuestionORM).where(
                OpenQuestionORM.id == qid,
                OpenQuestionORM.org_id == org_id,
            )
        )
        record = result.scalar_one_or_none()
        return _to_entity(record) if record else None

    async def list_by_meeting(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> list[OpenQuestion]:
        result = await self._db.execute(
            select(OpenQuestionORM)
            .where(
                OpenQuestionORM.meeting_id == meeting_id,
                OpenQuestionORM.org_id == org_id,
            )
            .order_by(OpenQuestionORM.created_at.asc())
        )
        return [_to_entity(record) for record in result.scalars().all()]

    async def update(self, question: OpenQuestion) -> OpenQuestion:
        result = await self._db.execute(
            select(OpenQuestionORM).where(OpenQuestionORM.id == question.id)
        )
        record = result.scalar_one()
        record.status = question.status
        record.answer = question.answer
        record.answered_by = question.answered_by
        record.answered_at = question.answered_at
        record.updated_at = question.updated_at
        await self._db.flush()
        return _to_entity(record)
