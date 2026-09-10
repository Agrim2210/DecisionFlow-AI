   
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


                                                                 
                                      
                                                                 

class UserReliabilityResponse(BaseModel):
       
    user_id: uuid.UUID
    reliability_score: float                          
    tasks_assigned: int
    tasks_completed: int
    tasks_on_time: int                                                    
    tasks_overdue: int
    tasks_cancelled: int
    completion_rate: float                                             
    snapshot_date: str                             


class MeetingAnalyticsResponse(BaseModel):
                                                       
    meeting_id: uuid.UUID
    decisions_count: int
    action_items_count: int
    unassigned_tasks: int
    risks_count: int
    critical_risks: int
    dependencies_count: int
    open_questions_count: int
    execution_rate: float                                                               


class UpcomingDeadlineResponse(BaseModel):
    task_id: str
    title: str
    due_date: str | None
    priority: str


                                                                 
                     
                                                                 

class TopPerformerResponse(BaseModel):
    user_id: str
    score: float


class AtRiskUserResponse(BaseModel):
    user_id: str
    score: float


class OrgDashboardResponse(BaseModel):
       
    org_id: uuid.UUID

                     
    total_meetings: int
    total_decisions: int

                    
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    blocked_tasks: int
    unassigned_tasks: int

                
    active_escalations: int

                 
    avg_reliability_score: float                           
    org_execution_rate: float                                       

                       
    top_performers: list[TopPerformerResponse]
    at_risk_users: list[AtRiskUserResponse]

    computed_at: str                                                              


class ReliabilityListResponse(BaseModel):
                                                                                 
    snapshots: list[UserReliabilityResponse]
    org_avg_score: float
    total_users: int


class ReliabilityTrendResponse(BaseModel):
                                                     
    user_id: uuid.UUID
    current_score: float
    trend: list[UserReliabilityResponse]                               
    trend_direction: str                                            
    change_pct: float                                                   


                                                                 
                      
                                                                 

class WorkerDashboardResponse(BaseModel):
       
    user_id: uuid.UUID

              
    my_tasks_total: int
    my_tasks_pending: int
    my_tasks_in_progress: int
    my_tasks_completed: int
    my_tasks_overdue: int
    my_tasks_blocked: int

                          
    my_reliability_score: float
    my_completion_rate: float

                           
    my_meetings_count: int

                            
    upcoming_deadlines: list[UpcomingDeadlineResponse]

    computed_at: str


                                                                 
         
                                                                 

def map_reliability_snapshot(s: Any) -> UserReliabilityResponse:
    return UserReliabilityResponse(
        user_id=s.user_id,
        reliability_score=round(float(s.reliability_score), 2),
        tasks_assigned=s.tasks_assigned,
        tasks_completed=s.tasks_completed,
        tasks_on_time=s.tasks_on_time,
        tasks_overdue=s.tasks_overdue,
        tasks_cancelled=s.tasks_cancelled,
        completion_rate=s.completion_rate,
        snapshot_date=s.snapshot_date.isoformat(),
    )


def map_org_dashboard(d: Any) -> OrgDashboardResponse:
    return OrgDashboardResponse(
        org_id=d.org_id,
        total_meetings=d.total_meetings,
        total_decisions=d.total_decisions,
        total_tasks=d.total_tasks,
        pending_tasks=d.pending_tasks,
        in_progress_tasks=getattr(d, "in_progress_tasks", 0),
        completed_tasks=d.completed_tasks,
        overdue_tasks=d.overdue_tasks,
        blocked_tasks=d.blocked_tasks,
        unassigned_tasks=d.unassigned_tasks,
        active_escalations=d.active_escalations,
        avg_reliability_score=round(float(d.avg_reliability_score), 2),
        org_execution_rate=round(float(d.org_execution_rate), 2),
        top_performers=[
            TopPerformerResponse(user_id=str(p["user_id"]), score=float(p["score"]))
            for p in (d.top_performers or [])
        ],
        at_risk_users=[
            AtRiskUserResponse(user_id=str(u["user_id"]), score=float(u["score"]))
            for u in (d.at_risk_users or [])
        ],
        computed_at=d.computed_at.isoformat(),
    )


def map_worker_dashboard(d: Any) -> WorkerDashboardResponse:
    return WorkerDashboardResponse(
        user_id=d.user_id,
        my_tasks_total=d.my_tasks_total,
        my_tasks_pending=d.my_tasks_pending,
        my_tasks_in_progress=getattr(d, "my_tasks_in_progress", 0),
        my_tasks_completed=d.my_tasks_completed,
        my_tasks_overdue=d.my_tasks_overdue,
        my_tasks_blocked=d.my_tasks_blocked,
        my_reliability_score=round(float(d.my_reliability_score), 2),
        my_completion_rate=round(
            (d.my_tasks_completed / d.my_tasks_total * 100) if d.my_tasks_total > 0 else 0.0, 2
        ),
        my_meetings_count=d.my_meetings_count,
        upcoming_deadlines=[
            UpcomingDeadlineResponse(
                task_id=str(t["task_id"]),
                title=t["title"],
                due_date=t.get("due_date"),
                priority=t.get("priority", "medium"),
            )
            for t in (d.upcoming_deadlines or [])
        ],
        computed_at=d.computed_at.isoformat(),
    )


def map_meeting_analytics(a: Any) -> MeetingAnalyticsResponse:
    return MeetingAnalyticsResponse(
        meeting_id=a.meeting_id,
        decisions_count=a.decisions_count,
        action_items_count=a.action_items_count,
        unassigned_tasks=a.unassigned_tasks,
        risks_count=a.risks_count,
        critical_risks=a.critical_risks,
        dependencies_count=a.dependencies_count,
        open_questions_count=a.open_questions_count,
        execution_rate=round(float(a.execution_rate), 2),
    )
