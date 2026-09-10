   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


                                                                
                                   
                                                                

@dataclass
class UserReliabilitySnapshot:
       
    id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    snapshot_date: datetime                                           
    tasks_assigned: int = 0                                     
    tasks_completed: int = 0                                    
    tasks_on_time: int = 0                                         
    tasks_overdue: int = 0                                        
    tasks_cancelled: int = 0                                               
    reliability_score: float = 100.0              
    created_at: datetime = field(default_factory=_now)

    @property
    def completion_rate(self) -> float:
                                                     
        if self.tasks_assigned == 0:
            return 100.0
        return round((self.tasks_completed / self.tasks_assigned) * 100, 2)

    @property
    def is_at_risk(self) -> bool:
                                                             
        return self.reliability_score < 70.0

    @property
    def is_high_performer(self) -> bool:
                                                                    
        return self.reliability_score >= 90.0


@dataclass
class MeetingAnalytics:
       
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID

                                                                      
    decisions_count: int = 0
    action_items_count: int = 0
    unassigned_tasks: int = 0
    risks_count: int = 0
    critical_risks: int = 0
    dependencies_count: int = 0
    open_questions_count: int = 0

                                                               
    execution_rate: float = 0.0                                    

    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def has_critical_risks(self) -> bool:
        return self.critical_risks > 0

    @property
    def is_well_assigned(self) -> bool:
                                            
        return self.unassigned_tasks == 0

    @property
    def execution_grade(self) -> str:
                                              
        if self.execution_rate >= 90:
            return "A"
        elif self.execution_rate >= 75:
            return "B"
        elif self.execution_rate >= 60:
            return "C"
        elif self.execution_rate >= 40:
            return "D"
        return "F"

    def update_execution_rate(self, rate: float) -> None:
        self.execution_rate = round(rate, 2)
        self.updated_at = _now()


                                                                
                                                          
                                                                

@dataclass
class OrgDashboard:
       
    org_id: uuid.UUID

                    
    total_meetings: int = 0
    total_decisions: int = 0
    total_tasks: int = 0

                           
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    blocked_tasks: int = 0
    unassigned_tasks: int = 0

                
    active_escalations: int = 0

                            
    avg_reliability_score: float = 100.0
    org_execution_rate: float = 0.0

                                             
    top_performers: list[dict[str, Any]] = field(default_factory=list)
    at_risk_users: list[dict[str, Any]] = field(default_factory=list)

    computed_at: datetime = field(default_factory=_now)

    def compute_execution_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return round((self.completed_tasks / self.total_tasks) * 100, 2)


@dataclass
class WorkerDashboard:
       
    user_id: uuid.UUID
    org_id: uuid.UUID

                       
    my_tasks_total: int = 0
    my_tasks_pending: int = 0
    my_tasks_in_progress: int = 0
    my_tasks_completed: int = 0
    my_tasks_overdue: int = 0
    my_tasks_blocked: int = 0

                          
    my_reliability_score: float = 100.0

              
    my_meetings_count: int = 0

                                  
    upcoming_deadlines: list[dict[str, Any]] = field(default_factory=list)

    computed_at: datetime = field(default_factory=_now)

    @property
    def my_completion_rate(self) -> float:
        if self.my_tasks_total == 0:
            return 100.0
        return round((self.my_tasks_completed / self.my_tasks_total) * 100, 2)

    @property
    def has_overdue(self) -> bool:
        return self.my_tasks_overdue > 0
