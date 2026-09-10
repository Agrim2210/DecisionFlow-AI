   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import structlog

from app.domains.meetings.application.commands import (
    DeleteMeetingCommand,
    PasteMeetingCommand,
    UpdateMeetingStatusCommand,
    UploadMeetingCommand,
)
from app.domains.meetings.application.queries import (
    GetMeetingQuery,
    GetProcessingStatusQuery,
    ListMeetingsQuery,
)
from app.domains.meetings.domain.entities import Meeting, MeetingSource, ProcessingStatus, Transcript
from app.domains.meetings.domain.exceptions import (
    DuplicateTranscriptError,
    FileTooLargeError,
    InvalidFileTypeError,
    MeetingNotFoundError,
)
from app.domains.meetings.domain.repositories import IMeetingRepository, ITranscriptRepository
from app.shared.exceptions import BadRequestError, PermissionDeniedError

logger = structlog.get_logger(__name__)

                    
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/vtt",
    "text/srt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
}
ALLOWED_EXTENSIONS = {".txt", ".vtt", ".srt", ".docx", ".md"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024          


@dataclass
class MeetingCreatedResult:
    meeting: Meeting
    transcript: Transcript


class MeetingService:
    def __init__(
        self,
        meeting_repo: IMeetingRepository,
        transcript_repo: ITranscriptRepository,
        s3_client: Any,                                                           
    ) -> None:
        self._meetings = meeting_repo
        self._transcripts = transcript_repo
        self._s3 = s3_client

                                                                    
    async def upload_meeting(self, cmd: UploadMeetingCommand) -> MeetingCreatedResult:
           
                  
        self._validate_file(cmd.filename, cmd.file_content, cmd.content_type)

                
        raw_text = self._decode_content(cmd.file_content, cmd.filename)

                     
        content_hash = Transcript.compute_hash(raw_text)
        existing = await self._meetings.exists_by_content_hash(content_hash, cmd.org_id)
        if existing:
            raise DuplicateTranscriptError(
                f"This transcript was already uploaded as meeting '{existing.title}' "
                f"(ID: {existing.id}). "
                "If this is a different meeting, please edit the transcript before uploading."
            )

                      
        meeting_id = uuid.uuid4()
        s3_key = f"orgs/{cmd.org_id}/meetings/{meeting_id}/raw/{cmd.filename}"
        await self._s3.upload(
            key=s3_key,
            content=cmd.file_content,
            content_type=cmd.content_type,
        )

                         
        title = cmd.title or self._title_from_filename(cmd.filename)

                               
        meeting = Meeting(
            id=meeting_id,
            org_id=cmd.org_id,
            created_by=cmd.uploaded_by,
            title=title,
            source=cmd.source,
            status=ProcessingStatus.UPLOADED,
            meeting_date=cmd.meeting_date,
            processing_meta={"filename": cmd.filename},
        )
        meeting = await self._meetings.create(meeting)

                                  
        transcript = Transcript(
            id=uuid.uuid4(),
            meeting_id=meeting.id,
            org_id=cmd.org_id,
            raw_s3_key=s3_key,
            raw_text=raw_text,
            content_hash=content_hash,
            word_count=len(raw_text.split()),
        )
        transcript = await self._transcripts.create(transcript)

                                                           
        self._dispatch_pipeline(meeting.id, cmd.org_id)

        logger.info(
            "meeting_uploaded",
            meeting_id=str(meeting.id),
            org_id=str(cmd.org_id),
            words=transcript.word_count,
        )

        return MeetingCreatedResult(meeting=meeting, transcript=transcript)

                                                                    
    async def paste_meeting(self, cmd: PasteMeetingCommand) -> MeetingCreatedResult:
                                              
        if not cmd.text.strip():
            from app.shared.exceptions import BadRequestError
            raise BadRequestError("Transcript text cannot be empty")

        raw_text = cmd.text.strip()

                     
        content_hash = Transcript.compute_hash(raw_text)
        existing = await self._meetings.exists_by_content_hash(content_hash, cmd.org_id)
        if existing:
            raise DuplicateTranscriptError(
                f"This exact transcript already exists as '{existing.title}'"
            )

                               
        meeting_id = uuid.uuid4()
        s3_key = f"orgs/{cmd.org_id}/meetings/{meeting_id}/raw/transcript.txt"
        await self._s3.upload(
            key=s3_key,
            content=raw_text.encode("utf-8"),
            content_type="text/plain",
        )

        title = cmd.title or self._title_from_text(raw_text)

        meeting = Meeting(
            id=meeting_id,
            org_id=cmd.org_id,
            created_by=cmd.pasted_by,
            title=title,
            source=MeetingSource.PASTE,
            status=ProcessingStatus.UPLOADED,
            meeting_date=cmd.meeting_date,
        )
        meeting = await self._meetings.create(meeting)

        transcript = Transcript(
            id=uuid.uuid4(),
            meeting_id=meeting.id,
            org_id=cmd.org_id,
            raw_s3_key=s3_key,
            raw_text=raw_text,
            content_hash=content_hash,
            word_count=len(raw_text.split()),
        )
        transcript = await self._transcripts.create(transcript)

        self._dispatch_pipeline(meeting.id, cmd.org_id)

        logger.info(
            "meeting_pasted",
            meeting_id=str(meeting.id),
            org_id=str(cmd.org_id),
            words=transcript.word_count,
        )

        return MeetingCreatedResult(meeting=meeting, transcript=transcript)

                                                                    
    async def get_meeting(self, query: GetMeetingQuery) -> Meeting:
        meeting = await self._meetings.get_by_id(query.meeting_id, query.org_id)
        if not meeting:
            raise MeetingNotFoundError()
        return meeting

    async def get_processing_status(self, query: GetProcessingStatusQuery) -> dict:
                                                                     
        meeting = await self._meetings.get_by_id(query.meeting_id, query.org_id)
        if not meeting:
            raise MeetingNotFoundError()
        return {
            "meeting_id": str(meeting.id),
            "status": meeting.status,
            "current_stage": meeting.processing_meta.get("current_stage"),
            "current_stage_name": meeting.processing_meta.get("current_stage_name"),
            "error": meeting.processing_meta.get("error"),
            "total_stages": 7,
            "progress_pct": self._stage_to_pct(
                meeting.processing_meta.get("current_stage", 0)
            ),
        }

    async def list_meetings(self, query: ListMeetingsQuery) -> list[Meeting]:
        return await self._meetings.list_by_org(
            org_id=query.org_id,
            limit=query.limit + 1,
            cursor_id=query.cursor_id,
            created_by=query.created_by,                           
            status=query.status_filter,
        )

    async def retry_pipeline(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> Meeting:
        meeting = await self._meetings.get_by_id(meeting_id, org_id)
        if not meeting:
            raise MeetingNotFoundError()

        if meeting.status == ProcessingStatus.COMPLETED:
            raise BadRequestError("Extraction is already completed for this meeting")
        if meeting.status in (ProcessingStatus.QUEUED, ProcessingStatus.PROCESSING):
            raise BadRequestError("Extraction is already in progress for this meeting")
        if meeting.status not in (ProcessingStatus.UPLOADED, ProcessingStatus.FAILED):
            raise BadRequestError(
                "Only uploaded or failed meetings can be retried"
            )

        meeting.transition_status(ProcessingStatus.QUEUED)
        meeting.set_stage(0, "retrying")
        meeting.processing_meta.pop("error", None)
        meeting.processing_meta.pop("failed_at_stage", None)
        meeting = await self._meetings.update(meeting)

        if not self._dispatch_pipeline(meeting.id, meeting.org_id):
            meeting.transition_status(ProcessingStatus.FAILED)
            meeting.record_error("Pipeline dispatch failed")
            meeting = await self._meetings.update(meeting)
            raise RuntimeError("Pipeline dispatch failed for retry")

        return meeting

                                                                    
    async def update_status(self, cmd: UpdateMeetingStatusCommand) -> Meeting:
        meeting = await self._meetings.get_by_id(cmd.meeting_id, cmd.org_id)
        if not meeting:
            raise MeetingNotFoundError()

        meeting.transition_status(cmd.new_status)

        if cmd.current_stage is not None:
            meeting.set_stage(cmd.current_stage, cmd.stage_name or "")

        if cmd.error:
            meeting.record_error(cmd.error, cmd.current_stage)

        if cmd.meta_updates:
            meeting.processing_meta.update(cmd.meta_updates)

        return await self._meetings.update(meeting)

                                                                    
    async def delete_meeting(self, cmd: DeleteMeetingCommand) -> None:
        meeting = await self._meetings.get_by_id(cmd.meeting_id, cmd.org_id)
        if not meeting:
            raise MeetingNotFoundError()

                                          
                                                                             
        await self._meetings.soft_delete(cmd.meeting_id, cmd.org_id)
        logger.info(
            "meeting_deleted",
            meeting_id=str(cmd.meeting_id),
            org_id=str(cmd.org_id),
            deleted_by=str(cmd.requested_by),
        )

                                                                    
    def _validate_file(self, filename: str, content: bytes, content_type: str) -> None:
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError()
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_CONTENT_TYPES:
            raise InvalidFileTypeError()

    def _decode_content(self, content: bytes, filename: str) -> str:
                                                            
        if filename.lower().endswith(".docx"):
            try:
                import docx2txt
                import io
                return docx2txt.process(io.BytesIO(content))
            except Exception:
                raise InvalidFileTypeError("Failed to read .docx file")
                                        
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")

    def _title_from_filename(self, filename: str) -> str:
        name = filename.rsplit(".", 1)[0]
        return name.replace("-", " ").replace("_", " ").title()

    def _title_from_text(self, text: str) -> str:
        first_line = text.strip().split("\n")[0][:80]
        return first_line or "Untitled Meeting"

    def _dispatch_pipeline(self, meeting_id: uuid.UUID, org_id: uuid.UUID) -> bool:
                                                   
        try:
            from app.shared.workers.pipeline_tasks import run_pipeline
            run_pipeline.delay(str(meeting_id), str(org_id))
            return True
        except Exception as e:
                                                                        
                                                                      
            logger.error(
                "pipeline_dispatch_failed",
                meeting_id=str(meeting_id),
                error=str(e),
            )
            return False

    @staticmethod
    def _stage_to_pct(stage: int) -> int:
        return min(int((stage / 7) * 100), 100)
