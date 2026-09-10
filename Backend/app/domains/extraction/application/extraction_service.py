                                                                      
from __future__ import annotations

import asyncio

from app.domains.extraction.application.commands import (
    AnswerQuestionCommand,
    AssignTaskCommand,
    UpdateDecisionCommand,
    UpdateRiskStatusCommand,
    UpdateTaskCommand,
    UpdateTaskStatusCommand,
)
from app.domains.extraction.application.decision_service import DecisionService
from app.domains.extraction.application.queries import (
    GetDecisionQuery,
    GetMeetingExtractionQuery,
    GetRiskQuery,
    GetTaskQuery,
    ListDecisionsQuery,
    ListQuestionsQuery,
    ListRisksQuery,
    ListTasksQuery,
)
from app.domains.extraction.application.risk_service import RiskService
from app.domains.extraction.application.task_service import TaskService
from app.domains.extraction.domain.entities import PipelineResult
from app.domains.extraction.domain.exceptions import OpenQuestionNotFoundError
from app.domains.extraction.domain.repositories import (
    IActionItemRepository,
    IDecisionRepository,
    IMemoryRepository,
    IOpenQuestionRepository,
    IRiskRepository,
)


class ExtractionService:
                                                                             

    def __init__(
        self,
        decision_repo: IDecisionRepository,
        task_repo: IActionItemRepository,
        risk_repo: IRiskRepository,
        question_repo: IOpenQuestionRepository,
        memory_repo: IMemoryRepository,
    ) -> None:
        self._decisions = DecisionService(decision_repo)
        self._tasks = TaskService(task_repo)
        self._risks = RiskService(risk_repo)
        self._questions = question_repo

    async def get_meeting_extraction(self, query: GetMeetingExtractionQuery) -> PipelineResult:
        decisions, tasks, risks, questions = await asyncio.gather(
            self._decisions.list(ListDecisionsQuery(org_id=query.org_id, meeting_id=query.meeting_id)),
            self._tasks.list(ListTasksQuery(org_id=query.org_id, meeting_id=query.meeting_id)),
            self._risks.list(ListRisksQuery(org_id=query.org_id, meeting_id=query.meeting_id)),
            self._questions.list_by_meeting(query.meeting_id, query.org_id),
        )
        return PipelineResult(
            meeting_id=query.meeting_id,
            org_id=query.org_id,
            decisions=decisions,
            action_items=tasks,
            risks=risks,
            open_questions=questions,
        )

    async def get_decision(self, query: GetDecisionQuery):
        return await self._decisions.get(query)

    async def list_decisions(self, query: ListDecisionsQuery):
        return await self._decisions.list(query)

    async def update_decision(self, command: UpdateDecisionCommand):
        return await self._decisions.update(command)

    async def get_task(self, query: GetTaskQuery):
        return await self._tasks.get(query)

    async def list_tasks(self, query: ListTasksQuery):
        return await self._tasks.list(query)

    async def update_task_status(self, command: UpdateTaskStatusCommand):
        return await self._tasks.update_status(command)

    async def update_task(self, command: UpdateTaskCommand):
        return await self._tasks.update(command)

    async def assign_task(self, command: AssignTaskCommand):
        return await self._tasks.assign(command)

    async def get_risk(self, query: GetRiskQuery):
        return await self._risks.get(query)

    async def list_risks(self, query: ListRisksQuery):
        return await self._risks.list(query)

    async def update_risk_status(self, command: UpdateRiskStatusCommand):
        return await self._risks.update_status(command)

    async def list_questions(self, query: ListQuestionsQuery):
        if query.meeting_id is None:
            return []
        return await self._questions.list_by_meeting(query.meeting_id, query.org_id)

    async def answer_question(self, command: AnswerQuestionCommand):
        question = await self._questions.get_by_id(command.question_id, command.org_id)
        if not question:
            raise OpenQuestionNotFoundError()
        question.answer_question(command.answer, command.answered_by)
        return await self._questions.update(question)
