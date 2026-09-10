   
from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    recipient_id: uuid.UUID
    event_type: str
    channel: str
    status: str
    subject: str
    body: str
    related_item_id: uuid.UUID | None
    related_item_type: str | None
    payload: dict[str, Any]
    is_read: bool
    sent_at: str | None
    read_at: str | None
    created_at: str


class InboxResponse(BaseModel):
    notifications: list[NotificationResponse]
    unread_count: int
    has_next: bool
    next_cursor: str | None


class UnreadCountResponse(BaseModel):
    unread_count: int


class EscalationResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    action_item_id: uuid.UUID
    policy_id: uuid.UUID
    current_level: int
    status: str
    history: list[dict[str, Any]]
    triggered_at: str
    resolved_at: str | None
    hours_active: float
    created_at: str


class EscalationListResponse(BaseModel):
    escalations: list[EscalationResponse]
    has_next: bool
    next_cursor: str | None


class PolicyLevelSchema(BaseModel):
    level: int = Field(..., ge=1, le=5)
    notify: str = Field(..., pattern=r"^(owner|admin|owner_role)$")
    after_hours: int = Field(..., ge=0, le=720)


class EscalationPolicyResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    is_default: bool
    trigger_after_hours: int
    levels: list[dict[str, Any]]
    created_at: str
    updated_at: str


class PolicyListResponse(BaseModel):
    policies: list[EscalationPolicyResponse]


class CreatePolicyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger_after_hours: int = Field(default=24, ge=1, le=720)
    levels: list[PolicyLevelSchema] = Field(default=[
        PolicyLevelSchema(level=1, notify="owner",      after_hours=0),
        PolicyLevelSchema(level=2, notify="admin",      after_hours=24),
        PolicyLevelSchema(level=3, notify="owner_role", after_hours=48),
    ])
    is_default: bool = False


class UpdatePolicyRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    trigger_after_hours: int | None = Field(default=None, ge=1, le=720)
    levels: list[PolicyLevelSchema] | None = None
    is_default: bool | None = None


class ResolveEscalationRequest(BaseModel):
    action: str = Field(..., pattern=r"^(resolve|dismiss)$")


def map_notification(n) -> NotificationResponse:
    return NotificationResponse(
        id=n.id, org_id=n.org_id, recipient_id=n.recipient_id,
        event_type=n.event_type, channel=n.channel, status=n.status,
        subject=n.subject, body=n.body,
        related_item_id=n.related_item_id, related_item_type=n.related_item_type,
        payload=n.payload or {}, is_read=n.is_read,
        sent_at=n.sent_at.isoformat() if n.sent_at else None,
        read_at=n.read_at.isoformat() if n.read_at else None,
        created_at=n.created_at.isoformat(),
    )


def map_escalation(e) -> EscalationResponse:
    return EscalationResponse(
        id=e.id, org_id=e.org_id, action_item_id=e.action_item_id,
        policy_id=e.policy_id, current_level=e.current_level, status=e.status,
        history=e.history or [], triggered_at=e.triggered_at.isoformat(),
        resolved_at=e.resolved_at.isoformat() if e.resolved_at else None,
        hours_active=round(e.hours_since_trigger(), 1),
        created_at=e.created_at.isoformat(),
    )


def map_policy(p) -> EscalationPolicyResponse:
    return EscalationPolicyResponse(
        id=p.id, org_id=p.org_id, name=p.name, is_default=p.is_default,
        trigger_after_hours=p.trigger_after_hours, levels=p.levels or [],
        created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
    )
