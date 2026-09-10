   
from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, Query, UploadFile

from app.domains.meetings.api.schemas import (
    MeetingCreatedResponse,
    MeetingDetailResponse,
    MeetingListResponse,
    MeetingRetryResponse,
    MeetingResponse,
    PasteMeetingRequest,
    ProcessingStatusResponse,
    map_meeting_to_response,
    map_transcript_to_response,
)
from app.domains.meetings.application.commands import (
    DeleteMeetingCommand,
    PasteMeetingCommand,
    UploadMeetingCommand,
)
from app.domains.meetings.application.meeting_service import MeetingService
from app.domains.meetings.application.queries import (
    GetMeetingQuery,
    GetProcessingStatusQuery,
    ListMeetingsQuery,
)
from app.domains.meetings.infra.repositories import (
    SQLMeetingRepository,
    SQLTranscriptRepository,
)
from app.shared.deps import AdminUser, CurrentUser, DBSession, MemberUser
from app.shared.pagination import encode_cursor

router = APIRouter(prefix="/meetings", tags=["Meetings"])


def _build_service(db) -> MeetingService:
    from app.domains.meetings.infra.s3_adapter import S3Client
    return MeetingService(
        meeting_repo=SQLMeetingRepository(db),
        transcript_repo=SQLTranscriptRepository(db),
        s3_client=S3Client(),
    )


                                                                    
@router.post(
    "/upload",
    response_model=MeetingCreatedResponse,
    status_code=201,
    summary="Upload a transcript file (.txt, .vtt, .srt, .docx, .md)",
)
async def upload_meeting(
    current_user: MemberUser,
    db: DBSession,
    file: UploadFile = File(..., description="Transcript file"),
    title: str | None = Form(default=None),
    source: str = Form(default="upload"),
) -> MeetingCreatedResponse:
    content = await file.read()
    service = _build_service(db)
    result = await service.upload_meeting(
        UploadMeetingCommand(
            org_id=current_user.org_id,
            uploaded_by=current_user.id,
            filename=file.filename or "transcript.txt",
            file_content=content,
            content_type=file.content_type or "text/plain",
            title=title,
            source=source,
        )
    )
    return MeetingCreatedResponse(meeting=map_meeting_to_response(result.meeting))


                                                                    
@router.post(
    "/paste",
    response_model=MeetingCreatedResponse,
    status_code=201,
    summary="Paste raw transcript text",
)
async def paste_meeting(
    body: PasteMeetingRequest,
    current_user: MemberUser,
    db: DBSession,
) -> MeetingCreatedResponse:
    service = _build_service(db)
    result = await service.paste_meeting(
        PasteMeetingCommand(
            org_id=current_user.org_id,
            pasted_by=current_user.id,
            text=body.text,
            title=body.title,
            meeting_date=body.meeting_date,
            source=body.source,
        )
    )
    return MeetingCreatedResponse(meeting=map_meeting_to_response(result.meeting))


                                                                   
@router.get(
    "",
    response_model=MeetingListResponse,
    summary="[Admin] List all meetings in the organization",
)
async def list_all_meetings(
    current_user: AdminUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> MeetingListResponse:
    service = _build_service(db)
    meetings = await service.list_meetings(
        ListMeetingsQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=_decode(cursor),
            created_by=None,                                       
            status_filter=status,
        )
    )
    return _build_list_response(meetings, limit)


                                                                    
@router.get(
    "/mine",
    response_model=MeetingListResponse,
    summary="[Worker] List meetings I uploaded",
)
async def list_my_meetings(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    status: str | None = Query(default=None),
) -> MeetingListResponse:
    service = _build_service(db)
    meetings = await service.list_meetings(
        ListMeetingsQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=_decode(cursor),
            created_by=current_user.id,                        
            status_filter=status,
        )
    )
    return _build_list_response(meetings, limit)


                                                                    
@router.get(
    "/{meeting_id}",
    response_model=MeetingDetailResponse,
    summary="Get meeting details",
)
async def get_meeting(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MeetingDetailResponse:
    service = _build_service(db)
    meeting = await service.get_meeting(
        GetMeetingQuery(meeting_id=meeting_id, org_id=current_user.org_id)
    )

                          
    from app.domains.meetings.infra.repositories import SQLTranscriptRepository
    transcript_repo = SQLTranscriptRepository(db)
    transcript = await transcript_repo.get_by_meeting_id(meeting_id, current_user.org_id)

    resp = MeetingDetailResponse(**map_meeting_to_response(meeting).model_dump())
    if transcript:
        resp.transcript = map_transcript_to_response(transcript)
    return resp


                                                                    
@router.get(
    "/{meeting_id}/status",
    response_model=ProcessingStatusResponse,
    summary="Get AI pipeline processing status (poll this endpoint)",
)
async def get_processing_status(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ProcessingStatusResponse:
    service = _build_service(db)
    status_dict = await service.get_processing_status(
        GetProcessingStatusQuery(meeting_id=meeting_id, org_id=current_user.org_id)
    )
    return ProcessingStatusResponse(**status_dict)


                                                                    
@router.delete(
    "/{meeting_id}",
    status_code=204,
    summary="Delete a meeting (soft delete)",
)
async def delete_meeting(
    meeting_id: uuid.UUID,
    current_user: MemberUser,
    db: DBSession,
) -> None:
    service = _build_service(db)
    await service.delete_meeting(
        DeleteMeetingCommand(
            meeting_id=meeting_id,
            org_id=current_user.org_id,
            requested_by=current_user.id,
        )
    )


@router.post(
    "/{meeting_id}/retry",
    response_model=MeetingRetryResponse,
    summary="Retry extraction for a meeting that was uploaded but not completed",
)
async def retry_meeting_extraction(
    meeting_id: uuid.UUID,
    current_user: MemberUser,
    db: DBSession,
) -> MeetingRetryResponse:
    service = _build_service(db)
    meeting = await service.retry_pipeline(meeting_id, current_user.org_id)
    return MeetingRetryResponse(
        meeting=map_meeting_to_response(meeting),
        message="Extraction retry started.",
    )


                                                                    
def _decode(cursor: str | None) -> uuid.UUID | None:
    if not cursor:
        return None
    try:
        from app.shared.pagination import decode_cursor
        return decode_cursor(cursor)
    except ValueError:
        return None


def _build_list_response(meetings: list, limit: int) -> MeetingListResponse:
    has_next = len(meetings) > limit
    page = meetings[:limit]
    return MeetingListResponse(
        meetings=[map_meeting_to_response(m) for m in page],
        has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )
