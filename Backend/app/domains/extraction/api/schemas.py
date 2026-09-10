   
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


                                                                 
                  
                                                                 

class DecisionResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    title: str
    description: str
    decision_type: str                                                                    
    status: str                                                           
    confidence_score: float                                          
    made_by: list[uuid.UUID]                                               
    effective_date: str | None
    review_date: str | None
    created_at: str
    updated_at: str


class ActionItemResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    decision_id: uuid.UUID | None                                        
    title: str
    description: str
    owner_id: uuid.UUID | None                                     
    owner_name: str | None = None                                  
    status: str                                                                                             
    priority: str                                                        
    due_date: str | None                           
    completed_at: str | None
    confidence_score: float
    is_overdue: bool                                                           
    is_unassigned: bool                                                        
    created_at: str
    updated_at: str


class RiskResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    related_item_id: uuid.UUID                                                       
    related_item_type: str                                           
    risk_type: str                                                                     
    severity: str                                                        
    description: str
    recommendation: str
    status: str                                                                      
    resolved_at: str | None
    created_at: str


class OpenQuestionResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    meeting_id: uuid.UUID
    question: str
    context: str                                                         
    status: str                                                      
    answer: str | None
    answered_by: uuid.UUID | None
    answered_at: str | None
    created_at: str


                                                                 
                        
                                                                 

class DecisionListResponse(BaseModel):
    decisions: list[DecisionResponse]
    has_next: bool
    next_cursor: str | None
    total: int | None = None                                                


class TaskListResponse(BaseModel):
    tasks: list[ActionItemResponse]
    has_next: bool
    next_cursor: str | None
    total: int | None = None


class RiskListResponse(BaseModel):
    risks: list[RiskResponse]
    total: int | None = None


class QuestionListResponse(BaseModel):
    questions: list[OpenQuestionResponse]


class MeetingExtractionResponse(BaseModel):
       
    meeting_id: uuid.UUID
    decisions: list[DecisionResponse]
    tasks: list[ActionItemResponse]
    risks: list[RiskResponse]
    open_questions: list[OpenQuestionResponse]
    summary: dict[str, int]                                                        


                                                                 
                 
                                                                 

class UpdateDecisionRequest(BaseModel):
                                                                  
    status: str | None = Field(
        default=None,
        pattern=r"^(active|superseded|cancelled)$",
        description="New status. active → superseded or cancelled only.",
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class UpdateTaskStatusRequest(BaseModel):
       
    status: str = Field(
        ...,
        pattern=r"^(pending|in_progress|completed|blocked|cancelled)$",
        description="New task status — must be a valid FSM transition from current status",
    )
    note: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional note explaining the status change",
    )


class UpdateTaskRequest(BaseModel):
                                                            
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    priority: str | None = Field(
        default=None,
        pattern=r"^(critical|high|medium|low)$",
    )
    due_date: datetime | None = Field(
        default=None,
        description="New deadline in ISO 8601 datetime format",
    )
    owner_id: uuid.UUID | None = Field(
        default=None,
        description="UUID of user to assign this task to",
    )


class AssignTaskRequest(BaseModel):
    owner_id: uuid.UUID = Field(
        ...,
        description="UUID of the user to assign this task to",
    )


class UpdateRiskStatusRequest(BaseModel):
    status: str = Field(
        ...,
        pattern=r"^(acknowledged|resolved|dismissed)$",
        description="New risk status. open → acknowledged → resolved | dismissed",
    )


class AnswerQuestionRequest(BaseModel):
    answer: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The answer text for this open question",
    )


                                                                 
                                            
                                                           
                                                                 

def map_decision(d: Any) -> DecisionResponse:
    return DecisionResponse(
        id=d.id,
        org_id=d.org_id,
        meeting_id=d.meeting_id,
        title=d.title,
        description=d.description,
        decision_type=d.decision_type,
        status=d.status,
        confidence_score=float(d.confidence_score),
        made_by=list(d.made_by or []),
        effective_date=d.effective_date.isoformat() if d.effective_date else None,
        review_date=d.review_date.isoformat() if d.review_date else None,
        created_at=d.created_at.isoformat(),
        updated_at=d.updated_at.isoformat(),
    )


def map_task(t: Any) -> ActionItemResponse:
    return ActionItemResponse(
        id=t.id,
        org_id=t.org_id,
        meeting_id=t.meeting_id,
        decision_id=t.decision_id,
        title=t.title,
        description=t.description,
        owner_id=t.owner_id,
        owner_name=getattr(t, "owner_name", None),
        status=t.status,
        priority=t.priority,
        due_date=t.due_date.isoformat() if t.due_date else None,
        completed_at=t.completed_at.isoformat() if t.completed_at else None,
        confidence_score=float(t.confidence_score),
        is_overdue=t.is_overdue,
        is_unassigned=t.is_unassigned,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


def map_risk(r: Any) -> RiskResponse:
    return RiskResponse(
        id=r.id,
        org_id=r.org_id,
        meeting_id=r.meeting_id,
        related_item_id=r.related_item_id,
        related_item_type=r.related_item_type,
        risk_type=r.risk_type,
        severity=r.severity,
        description=r.description,
        recommendation=r.recommendation,
        status=r.status,
        resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
        created_at=r.created_at.isoformat(),
    )


def map_question(q: Any) -> OpenQuestionResponse:
    return OpenQuestionResponse(
        id=q.id,
        org_id=q.org_id,
        meeting_id=q.meeting_id,
        question=q.question,
        context=q.context,
        status=q.status,
        answer=q.answer,
        answered_by=q.answered_by,
        answered_at=q.answered_at.isoformat() if q.answered_at else None,
        created_at=q.created_at.isoformat(),
    )
