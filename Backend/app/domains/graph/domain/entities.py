   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


class DependencyType:
       
    FINISH_TO_START  = "finish_to_start"
    START_TO_START   = "start_to_start"
    FINISH_TO_FINISH = "finish_to_finish"
    ALL = frozenset({FINISH_TO_START, START_TO_START, FINISH_TO_FINISH})


class DetectedBy:
                                            
    AI     = "ai"                                     
    MANUAL = "manual"                             


@dataclass
class TaskDependency:
       
    id: uuid.UUID
    org_id: uuid.UUID
    upstream_id: uuid.UUID                                
    downstream_id: uuid.UUID                                         
    dependency_type: str = DependencyType.FINISH_TO_START
    detected_by: str = DetectedBy.AI
    confidence_score: float = 1.0                                              
    created_by: uuid.UUID | None = None                                    
    created_at: datetime = field(default_factory=_now)

    @property
    def is_ai_detected(self) -> bool:
        return self.detected_by == DetectedBy.AI

    @property
    def is_manual(self) -> bool:
        return self.detected_by == DetectedBy.MANUAL

    @property
    def is_high_confidence(self) -> bool:
        return self.confidence_score >= 0.85


@dataclass
class DependencyGraph:
       
    meeting_id: uuid.UUID
    org_id: uuid.UUID
    nodes: list[dict]                                                      
    edges: list[dict]                                                            

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def is_empty(self) -> bool:
        return len(self.edges) == 0
