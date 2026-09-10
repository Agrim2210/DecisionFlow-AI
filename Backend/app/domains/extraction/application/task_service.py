   
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

from app.domains.extraction.application.commands import (
    AssignTaskCommand,
    UpdateTaskCommand,
    UpdateTaskStatusCommand,
)
from app.domains.extraction.application.queries import GetTaskQuery, ListTasksQuery
from app.domains.extraction.domain.entities import ActionItem
from app.domains.extraction.domain.events import TaskAssigned, TaskStatusChanged
from app.domains.extraction.domain.exceptions import ActionItemNotFoundError
from app.domains.extraction.domain.repositories import IActionItemRepository

logger = structlog.get_logger(__name__)


class TaskService:

    def __init__(
        self,
        task_repo: IActionItemRepository,
        event_publisher=None,
    ) -> None:
        self._repo = task_repo
        self._publish = event_publisher

    async def get(self, query: GetTaskQuery) -> ActionItem:
        t = await self._repo.get_by_id(query.task_id, query.org_id)
        if not t:
            raise ActionItemNotFoundError()
        return t

    async def list(self, query: ListTasksQuery) -> list[ActionItem]:
        if query.meeting_id:
            tasks = await self._repo.list_by_meeting(query.meeting_id, query.org_id)
            if query.owner_id:
                tasks = [t for t in tasks if t.owner_id == query.owner_id]
            if query.status:
                tasks = [t for t in tasks if t.status == query.status]
            return tasks
        return await self._repo.list_by_org(
            org_id=query.org_id,
            limit=query.limit + 1,
            cursor_id=query.cursor_id,
            owner_id=query.owner_id,                                                 
            status=query.status,
            overdue_only=query.overdue_only,
        )

    async def update_status(self, cmd: UpdateTaskStatusCommand) -> ActionItem:
        task = await self._repo.get_by_id(cmd.task_id, cmd.org_id)
        if not task:
            raise ActionItemNotFoundError()

        old_status = task.status
        task.transition(cmd.new_status)                                                 
        updated = await self._repo.update(task)

        logger.info(
            "task_status_changed",
            task_id=str(cmd.task_id),
            old=old_status,
            new=cmd.new_status,
            by=str(cmd.updated_by),
        )

        if self._publish:
            await self._safe_publish(TaskStatusChanged.create(
                org_id=cmd.org_id, task_id=cmd.task_id,
                old_status=old_status, new_status=cmd.new_status,
                changed_by=cmd.updated_by,
            ))

        return updated

    async def assign(self, cmd: AssignTaskCommand) -> ActionItem:
        task = await self._repo.get_by_id(cmd.task_id, cmd.org_id)
        if not task:
            raise ActionItemNotFoundError()

        old_owner = task.owner_id
        task.owner_id = cmd.owner_id
        task.updated_at = datetime.now(timezone.utc)
        updated = await self._repo.update(task)

        logger.info(
            "task_assigned",
            task_id=str(cmd.task_id),
            old_owner=str(old_owner) if old_owner else None,
            new_owner=str(cmd.owner_id),
            by=str(cmd.assigned_by),
        )

        if self._publish:
            await self._safe_publish(TaskAssigned.create(
                org_id=cmd.org_id, task_id=cmd.task_id,
                new_owner_id=cmd.owner_id, assigned_by=cmd.assigned_by,
            ))

        return updated

    async def update(self, cmd: UpdateTaskCommand) -> ActionItem:
        task = await self._repo.get_by_id(cmd.task_id, cmd.org_id)
        if not task:
            raise ActionItemNotFoundError()

        if cmd.title is not None:
            task.title = cmd.title
        if cmd.description is not None:
            task.description = cmd.description
        if cmd.priority is not None:
            task.priority = cmd.priority
        if cmd.due_date is not None:
            task.due_date = cmd.due_date
        if cmd.owner_id is not None:
            task.owner_id = cmd.owner_id

        task.updated_at = datetime.now(timezone.utc)
        return await self._repo.update(task)

    async def scan_and_mark_overdue(self, org_id: uuid.UUID) -> int:
           
        now = datetime.now(timezone.utc)
        overdue_tasks = await self._repo.get_overdue(org_id, now)
        count = 0
        for task in overdue_tasks:
            if task.status not in ("overdue", "completed", "cancelled"):
                task.mark_overdue()
                await self._repo.update(task)
                count += 1
        if count:
            logger.info("tasks_marked_overdue", org_id=str(org_id), count=count)
        return count

    async def _safe_publish(self, event) -> None:
        try:
            await self._publish(event)
        except Exception as exc:
            logger.warning("event_publish_failed", error=str(exc))
