                                                       
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SendNotificationCommand:
    org_id: uuid.UUID
    recipient_id: uuid.UUID
    event_type: str
    channels: list[str]
    subject: str
    body: str
    payload: dict[str, Any] = field(default_factory=dict)
    related_item_id: uuid.UUID | None = None
    related_item_type: str | None = None


@dataclass(frozen=True)
class MarkNotificationReadCommand:
    notif_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID


@dataclass(frozen=True)
class MarkAllReadCommand:
    org_id: uuid.UUID
    user_id: uuid.UUID


@dataclass(frozen=True)
class TriggerEscalationCommand:
    org_id: uuid.UUID
    action_item_id: uuid.UUID
    action_item_title: str
    owner_id: uuid.UUID | None
    due_date_str: str
    meeting_title: str = ""


@dataclass(frozen=True)
class AdvanceEscalationCommand:
    escalation_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ResolveEscalationCommand:
    escalation_id: uuid.UUID
    org_id: uuid.UUID
    resolved_by: uuid.UUID


@dataclass(frozen=True)
class DismissEscalationCommand:
    escalation_id: uuid.UUID
    org_id: uuid.UUID
    dismissed_by: uuid.UUID


@dataclass(frozen=True)
class CreatePolicyCommand:
    org_id: uuid.UUID
    name: str
    trigger_after_hours: int = 24
    levels: list[dict[str, Any]] = field(default_factory=list)
    is_default: bool = False


@dataclass(frozen=True)
class UpdatePolicyCommand:
    policy_id: uuid.UUID
    org_id: uuid.UUID
    name: str | None = None
    trigger_after_hours: int | None = None
    levels: list[dict[str, Any]] | None = None
    is_default: bool | None = None
