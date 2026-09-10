   
from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.domains.graph.api.schemas import (
    AddDependencyRequest,
    DependencyResponse,
    MeetingGraphResponse,
    TaskDependenciesResponse,
    map_dependency,
    map_graph,
    map_task_dependencies,
)
from app.domains.graph.application.commands import (
    AddDependencyCommand,
    RemoveDependencyCommand,
)
from app.domains.graph.application.cycle_detector import CycleDetector
from app.domains.graph.application.dependency_service import DependencyServiceWithDB
from app.domains.graph.application.queries import (
    GetMeetingGraphQuery,
    GetTaskDependenciesQuery,
)
from app.domains.graph.infra.dependency_repo import SQLDependencyRepository
from app.shared.deps import CurrentUser, DBSession, MemberUser

router = APIRouter(tags=["Dependency Graph"])


                                                                     

def _svc(db) -> DependencyServiceWithDB:
       
    return DependencyServiceWithDB(
        dep_repo=SQLDependencyRepository(db),
        db=db,
        cycle_detector=CycleDetector(),
    )


                                                                    

@router.get(
    "/meetings/{meeting_id}/graph",
    response_model=MeetingGraphResponse,
    summary="Get dependency graph for a meeting",
    description=(
        "Returns all task nodes and dependency edges for this meeting, "
        "formatted for interactive DAG visualization. "
        "Nodes are enriched with task status, priority, owner and overdue flags. "
        "Available once meeting pipeline status is `completed`."
    ),
)
async def get_meeting_graph(
    meeting_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> MeetingGraphResponse:
    svc = _svc(db)
    graph = await svc.get_meeting_graph(
        GetMeetingGraphQuery(
            meeting_id=meeting_id,
            org_id=current_user.org_id,
        )
    )
    return map_graph(graph)


                                                                    

@router.get(
    "/tasks/{task_id}/dependencies",
    response_model=TaskDependenciesResponse,
    summary="Get all dependencies for a specific task",
    description=(
        "Returns two lists: `blockers` (tasks this task is waiting on) "
        "and `dependents` (tasks waiting on this task to complete). "
        "Use this to render the dependency panel on the task detail page."
    ),
)
async def get_task_dependencies(
    task_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> TaskDependenciesResponse:
    svc = _svc(db)
    deps = await svc.get_task_dependencies(
        GetTaskDependenciesQuery(
            task_id=task_id,
            org_id=current_user.org_id,
        )
    )
    return map_task_dependencies(task_id, deps)


                                                                    

@router.post(
    "/dependencies",
    response_model=DependencyResponse,
    status_code=201,
    summary="[Member] Manually add a dependency between two tasks",
    description=(
        "Adds a directed dependency edge: upstream_id → downstream_id. "
        "The API enforces three rules before persisting:\n"
        "1. No self-loops (a task cannot depend on itself)\n"
        "2. No duplicates (the same edge cannot be added twice)\n"
        "3. No cycles (the resulting graph must remain a DAG)\n\n"
        "All three validations return a 400 error with a descriptive message."
    ),
)
async def add_dependency(
    body: AddDependencyRequest,
    current_user: MemberUser,
    db: DBSession,
) -> DependencyResponse:
    svc = _svc(db)
    dep = await svc.add_dependency(
        AddDependencyCommand(
            org_id=current_user.org_id,
            upstream_id=body.upstream_id,
            downstream_id=body.downstream_id,
            dependency_type=body.dependency_type,
            created_by=current_user.id,
        )
    )
    return map_dependency(dep)


                                                                    

@router.delete(
    "/dependencies/{dep_id}",
    status_code=204,
    summary="[Member] Remove a task dependency",
    description=(
        "Permanently removes a dependency edge. "
        "Both AI-detected and manually-added edges can be removed. "
        "This does not affect the tasks themselves."
    ),
)
async def remove_dependency(
    dep_id: uuid.UUID,
    current_user: MemberUser,
    db: DBSession,
) -> None:
    svc = _svc(db)
    await svc.remove_dependency(
        RemoveDependencyCommand(
            dep_id=dep_id,
            org_id=current_user.org_id,
            removed_by=current_user.id,
        )
    )
