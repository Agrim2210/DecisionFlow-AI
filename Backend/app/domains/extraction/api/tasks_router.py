   
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.domains.extraction.api.schemas import (
    ActionItemResponse,
    AssignTaskRequest,
    TaskListResponse,
    UpdateTaskRequest,
    UpdateTaskStatusRequest,
    map_task,
)
from app.domains.extraction.application.commands import (
    AssignTaskCommand,
    UpdateTaskCommand,
    UpdateTaskStatusCommand,
)
from app.domains.extraction.application.extraction_service import ExtractionService
from app.domains.extraction.application.queries import (
    GetTaskQuery,
    ListTasksQuery,
)
from app.domains.extraction.infra.decision_repo import SQLDecisionRepository
from app.domains.extraction.infra.task_repo import SQLActionItemRepository
from app.domains.extraction.infra.risk_repo import SQLRiskRepository
from app.domains.extraction.infra.memory_repo import SQLMemoryRepository
from app.domains.extraction.infra.repositories import SQLOpenQuestionRepository
from app.shared.deps import AdminUser, CurrentUser, DBSession, MemberUser
from app.shared.pagination import decode_cursor, encode_cursor

router = APIRouter(tags=["Tasks"])


                                                                     

def _svc(db) -> ExtractionService:
    return ExtractionService(
        decision_repo=SQLDecisionRepository(db),
        task_repo=SQLActionItemRepository(db),
        risk_repo=SQLRiskRepository(db),
        question_repo=SQLOpenQuestionRepository(db),
        memory_repo=SQLMemoryRepository(db),
    )


def _decode(cursor: str | None) -> uuid.UUID | None:
    if not cursor:
        return None
    try:
        return decode_cursor(cursor)
    except ValueError:
        return None


def _paginate(tasks: list, limit: int) -> TaskListResponse:
    has_next = len(tasks) > limit
    page = tasks[:limit]
    return TaskListResponse(
        tasks=[map_task(t) for t in page],
        has_next=has_next,
        next_cursor=encode_cursor(page[-1].id) if has_next and page else None,
    )


                                                                    

@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="[Admin] List all tasks across the organization",
    description=(
        "Returns tasks from all users. Filter by `owner_id`, `status`, "
        "or use `overdue_only=true` to see all overdue tasks across the org. "
        "Sorted by due_date ascending (soonest first, nulls last)."
    ),
)
async def list_all_tasks(
    current_user: AdminUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    owner_id: uuid.UUID | None = Query(
        default=None,
        description="Filter by a specific owner's UUID",
    ),
    status: str | None = Query(
        default=None,
        pattern=r"^(pending|in_progress|completed|blocked|cancelled|overdue)$",
    ),
    overdue_only: bool = Query(
        default=False,
        description="Return only overdue tasks",
    ),
) -> TaskListResponse:
    svc = _svc(db)
    tasks = await svc.list_tasks(
        ListTasksQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=_decode(cursor),
            owner_id=owner_id,                                
            status=status,
            overdue_only=overdue_only,
        )
    )
    return _paginate(tasks, limit)


                                                                    

@router.get(
    "/tasks/mine",
    response_model=TaskListResponse,
    summary="[Worker] List tasks assigned to me",
    description=(
        "Returns only tasks where owner = the current user. "
        "Use `status` to filter and `overdue_only=true` to see your overdue items."
    ),
)
async def list_my_tasks(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    status: str | None = Query(
        default=None,
        pattern=r"^(pending|in_progress|completed|blocked|cancelled|overdue)$",
    ),
    overdue_only: bool = Query(default=False),
) -> TaskListResponse:
    svc = _svc(db)
    tasks = await svc.list_tasks(
        ListTasksQuery(
            org_id=current_user.org_id,
            limit=limit,
            cursor_id=_decode(cursor),
            owner_id=current_user.id,                                           
            status=status,
            overdue_only=overdue_only,
        )
    )
    return _paginate(tasks, limit)


                                                                    

@router.get(
    "/meetings/{meeting_id}/tasks",
    response_model=list[ActionItemResponse],
    summary="Get all tasks extracted from a specific meeting",
)
async def list_meeting_tasks(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> list[ActionItemResponse]:
    svc = _svc(db)
    tasks = await svc.list_tasks(
        ListTasksQuery(
            org_id=current_user.org_id,
            meeting_id=meeting_id,
        )
    )
    return [map_task(t) for t in tasks]


                                                                   

@router.get(
    "/tasks/{task_id}",
    response_model=ActionItemResponse,
    summary="Get a specific task by ID",
)
async def get_task(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> ActionItemResponse:
    svc = _svc(db)
    task = await svc.get_task(
        GetTaskQuery(task_id=task_id, org_id=current_user.org_id)
    )
    return map_task(task)


                                                                    

@router.patch(
    "/tasks/{task_id}/status",
    response_model=ActionItemResponse,
    summary="Update task status (worker self-service)",
    description=(
        "Update the status of any task the current user can see. "
        "Domain enforces FSM transitions — invalid transitions return 400. "
        "Allowed: pending→in_progress, in_progress→completed|blocked|cancelled, etc."
    ),
)
async def update_task_status(
    task_id: uuid.UUID,
    body: UpdateTaskStatusRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> ActionItemResponse:
    svc = _svc(db)
    task = await svc.update_task_status(
        UpdateTaskStatusCommand(
            task_id=task_id,
            org_id=current_user.org_id,
            updated_by=current_user.id,
            new_status=body.status,
            note=body.note,
        )
    )
    return map_task(task)


                                                                    

@router.patch(
    "/tasks/{task_id}",
    response_model=ActionItemResponse,
    summary="[Member] Update task details (title, priority, due date, owner)",
    description=(
        "Partial update — only include fields you want to change. "
        "To change only status use PATCH /tasks/{id}/status instead."
    ),
)
async def update_task(
    task_id: uuid.UUID,
    body: UpdateTaskRequest,
    current_user: MemberUser,
    db: DBSession,
) -> ActionItemResponse:
    svc = _svc(db)
    task = await svc.update_task(
        UpdateTaskCommand(
            task_id=task_id,
            org_id=current_user.org_id,
            updated_by=current_user.id,
            title=body.title,
            description=body.description,
            priority=body.priority,
            due_date=body.due_date,
            owner_id=body.owner_id,
        )
    )
    return map_task(task)


                                                                    

@router.patch(
    "/tasks/{task_id}/assign",
    response_model=ActionItemResponse,
    summary="[Admin] Assign or reassign a task to a user",
    description="Assign this task to any user in the organization.",
)
async def assign_task(
    task_id: uuid.UUID,
    body: AssignTaskRequest,
    current_user: AdminUser,
    db: DBSession,
) -> ActionItemResponse:
    svc = _svc(db)
    task = await svc.assign_task(
        AssignTaskCommand(
            task_id=task_id,
            org_id=current_user.org_id,
            assigned_by=current_user.id,
            owner_id=body.owner_id,
        )
    )
    return map_task(task)
