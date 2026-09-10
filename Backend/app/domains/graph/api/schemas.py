   
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


                                                                 
                 
                                                                 

class AddDependencyRequest(BaseModel):
    upstream_id: uuid.UUID = Field(
        ...,
        description="Task that must complete FIRST (the blocker)",
    )
    downstream_id: uuid.UUID = Field(
        ...,
        description="Task that is BLOCKED until upstream completes",
    )
    dependency_type: str = Field(
        default="finish_to_start",
        pattern=r"^(finish_to_start|start_to_start|finish_to_finish)$",
        description=(
            "finish_to_start: downstream cannot start until upstream finishes (most common). "
            "start_to_start: downstream cannot start until upstream starts. "
            "finish_to_finish: downstream cannot finish until upstream finishes."
        ),
    )


                                                                 
                  
                                                                 

class DependencyResponse(BaseModel):
                                                                                
    id: uuid.UUID
    org_id: uuid.UUID
    upstream_id: uuid.UUID
    downstream_id: uuid.UUID
    dependency_type: str
    dependency_type_label: str                                              
    detected_by: str                                      
    confidence_score: float
    created_at: str


class GraphNodeResponse(BaseModel):
       
    id: str                                                   
    label: str                                                      
    status: str                                                                                 
    priority: str                                                        
    owner_id: str | None                                      
    is_overdue: bool
    is_unassigned: bool
    meeting_id: str


class GraphEdgeResponse(BaseModel):
                                                                        
    id: str                                                         
    source: str                                              
    target: str                                                
    type: str                                                    
    label: str                                             
    detected_by: str                                      
    confidence_score: float


class MeetingGraphResponse(BaseModel):
       
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]
    node_count: int
    edge_count: int
    has_cycles: bool = False                                                         


class TaskDependenciesResponse(BaseModel):
       
    task_id: uuid.UUID
    blockers: list[DependencyResponse]                                        
    dependents: list[DependencyResponse]                                    
    total_blockers: int
    total_dependents: int


                                                                 
         
                                                                 

_TYPE_LABELS = {
    "finish_to_start":  "Finish → Start",
    "start_to_start":   "Start → Start",
    "finish_to_finish": "Finish → Finish",
}


def map_dependency(dep: Any) -> DependencyResponse:
    return DependencyResponse(
        id=dep.id,
        org_id=dep.org_id,
        upstream_id=dep.upstream_id,
        downstream_id=dep.downstream_id,
        dependency_type=dep.dependency_type,
        dependency_type_label=_TYPE_LABELS.get(dep.dependency_type, dep.dependency_type),
        detected_by=dep.detected_by,
        confidence_score=float(dep.confidence_score),
        created_at=dep.created_at.isoformat(),
    )


def map_graph(graph: Any) -> MeetingGraphResponse:
    nodes = [
        GraphNodeResponse(
            id=n["id"],
            label=n["label"],
            status=n.get("status", "unknown"),
            priority=n.get("priority", "medium"),
            owner_id=n.get("owner_id"),
            is_overdue=n.get("is_overdue", False),
            is_unassigned=n.get("is_unassigned", True),
            meeting_id=n.get("meeting_id", ""),
        )
        for n in graph.nodes
    ]
    edges = [
        GraphEdgeResponse(
            id=e["id"],
            source=e["source"],
            target=e["target"],
            type=e.get("type", "finish_to_start"),
            label=e.get("label", "Finish → Start"),
            detected_by=e.get("detected_by", "ai"),
            confidence_score=float(e.get("confidence_score", 1.0)),
        )
        for e in graph.edges
    ]
    return MeetingGraphResponse(
        meeting_id=graph.meeting_id,
        org_id=graph.org_id,
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )


def map_task_dependencies(
    task_id: uuid.UUID, all_deps: list[Any]
) -> TaskDependenciesResponse:
       
    blockers = [dep for dep in all_deps if dep.downstream_id == task_id]
    dependents = [dep for dep in all_deps if dep.upstream_id == task_id]
    return TaskDependenciesResponse(
        task_id=task_id,
        blockers=[map_dependency(d) for d in blockers],
        dependents=[map_dependency(d) for d in dependents],
        total_blockers=len(blockers),
        total_dependents=len(dependents),
    )
