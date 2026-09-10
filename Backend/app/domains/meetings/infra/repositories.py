   
from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.meetings.domain.entities import Meeting, ProcessingStatus, Transcript
from app.domains.meetings.domain.repositories import IMeetingRepository, ITranscriptRepository
from app.domains.meetings.infra.orm_models import MeetingORM, TranscriptORM


                                                                     
def _meeting_to_entity(orm: MeetingORM) -> Meeting:
    return Meeting(
        id=orm.id,
        org_id=orm.org_id,
        created_by=orm.created_by,
        title=orm.title,
        source=orm.source,
        status=orm.status,
        meeting_date=orm.meeting_date,
        duration_seconds=orm.duration_seconds,
        participant_ids=list(orm.participant_ids or []),
        processing_meta=dict(orm.processing_meta or {}),
        created_at=orm.created_at,
        updated_at=orm.updated_at,
        deleted_at=orm.deleted_at,
    )


def _transcript_to_entity(orm: TranscriptORM) -> Transcript:
    return Transcript(
        id=orm.id,
        meeting_id=orm.meeting_id,
        org_id=orm.org_id,
        raw_s3_key=orm.raw_s3_key,
        normalized_s3_key=orm.normalized_s3_key,
        raw_text=orm.raw_text,
        content_hash=orm.content_hash,
        word_count=orm.word_count,
        speaker_map=dict(orm.speaker_map or {}),
        created_at=orm.created_at,
    )


class SQLMeetingRepository(IMeetingRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, meeting: Meeting) -> Meeting:
        orm = MeetingORM(
            id=meeting.id,
            org_id=meeting.org_id,
            created_by=meeting.created_by,
            title=meeting.title,
            source=meeting.source,
            status=meeting.status,
            meeting_date=meeting.meeting_date,
            duration_seconds=meeting.duration_seconds,
            participant_ids=meeting.participant_ids,
            processing_meta=meeting.processing_meta,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _meeting_to_entity(orm)

    async def get_by_id(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> Meeting | None:
        result = await self._db.execute(
            select(MeetingORM).where(
                MeetingORM.id == meeting_id,
                MeetingORM.org_id == org_id,
                MeetingORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _meeting_to_entity(orm) if orm else None

    async def list_by_org(
        self,
        org_id: uuid.UUID,
        limit: int = 50,
        cursor_id: uuid.UUID | None = None,
        created_by: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[Meeting]:
        query = select(MeetingORM).where(
            MeetingORM.org_id == org_id,
            MeetingORM.deleted_at.is_(None),
        )
        if created_by:
            query = query.where(MeetingORM.created_by == created_by)
        if status:
            query = query.where(MeetingORM.status == status)
        if cursor_id:
            query = query.where(MeetingORM.id > cursor_id)
        query = query.order_by(MeetingORM.created_at.desc()).limit(limit)
        result = await self._db.execute(query)
        return [_meeting_to_entity(r) for r in result.scalars().all()]

    async def update(self, meeting: Meeting) -> Meeting:
        result = await self._db.execute(
            select(MeetingORM).where(MeetingORM.id == meeting.id)
        )
        orm = result.scalar_one()
        orm.title = meeting.title
        orm.status = meeting.status
        orm.processing_meta = meeting.processing_meta
        orm.duration_seconds = meeting.duration_seconds
        orm.participant_ids = meeting.participant_ids
        orm.deleted_at = meeting.deleted_at
        await self._db.flush()
        await self._db.refresh(orm)
        return _meeting_to_entity(orm)

    async def soft_delete(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> None:
        from datetime import datetime, timezone
        await self._db.execute(
            update(MeetingORM)
            .where(MeetingORM.id == meeting_id, MeetingORM.org_id == org_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    async def exists_by_content_hash(self, content_hash: str, org_id: uuid.UUID) -> Meeting | None:
        result = await self._db.execute(
            select(MeetingORM)
            .join(TranscriptORM, TranscriptORM.meeting_id == MeetingORM.id)
            .where(
                TranscriptORM.content_hash == content_hash,
                MeetingORM.org_id == org_id,
                MeetingORM.deleted_at.is_(None),
            )
        )
        orm = result.scalar_one_or_none()
        return _meeting_to_entity(orm) if orm else None


class SQLTranscriptRepository(ITranscriptRepository):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, transcript: Transcript) -> Transcript:
        orm = TranscriptORM(
            id=transcript.id,
            meeting_id=transcript.meeting_id,
            org_id=transcript.org_id,
            raw_s3_key=transcript.raw_s3_key,
            normalized_s3_key=transcript.normalized_s3_key,
            raw_text=transcript.raw_text,
            content_hash=transcript.content_hash,
            word_count=transcript.word_count,
            speaker_map=transcript.speaker_map,
        )
        self._db.add(orm)
        await self._db.flush()
        await self._db.refresh(orm)
        return _transcript_to_entity(orm)

    async def get_by_meeting_id(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> Transcript | None:
        result = await self._db.execute(
            select(TranscriptORM).where(
                TranscriptORM.meeting_id == meeting_id,
                TranscriptORM.org_id == org_id,
            )
        )
        orm = result.scalar_one_or_none()
        return _transcript_to_entity(orm) if orm else None

    async def update(self, transcript: Transcript) -> Transcript:
        result = await self._db.execute(
            select(TranscriptORM).where(TranscriptORM.id == transcript.id)
        )
        orm = result.scalar_one()
        orm.normalized_s3_key = transcript.normalized_s3_key
        orm.raw_text = transcript.raw_text
        orm.word_count = transcript.word_count
        orm.speaker_map = transcript.speaker_map
        await self._db.flush()
        await self._db.refresh(orm)
        return _transcript_to_entity(orm)
