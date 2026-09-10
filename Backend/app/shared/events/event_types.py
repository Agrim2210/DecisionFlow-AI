from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


                                                                    

class Stream:
    IDENTITY      = "stream:identity"
    MEETINGS      = "stream:meetings"
    EXTRACTION    = "stream:extraction"
    NOTIFICATIONS = "stream:notifications"
    ANALYTICS     = "stream:analytics"
    GRAPH         = "stream:graph"


                                                                     

class EventType:
              
    USER_REGISTERED         = "user.registered"
    USER_INVITED            = "user.invited"
    USER_LOGGED_IN          = "user.logged_in"
    ROLE_CHANGED            = "user.role_changed"
    TOKEN_REUSE_DETECTED    = "user.token_reuse_detected"

              
    MEETING_UPLOADED        = "meeting.uploaded"
    MEETING_DELETED         = "meeting.deleted"
    PIPELINE_STARTED        = "pipeline.started"
    PIPELINE_COMPLETED      = "pipeline.completed"
    PIPELINE_FAILED         = "pipeline.failed"

                
    DECISION_EXTRACTED      = "decision.extracted"
    TASK_CREATED            = "action_item.created"
    TASK_STATUS_CHANGED     = "action_item.status_changed"
    TASK_ASSIGNED           = "action_item.assigned"
    RISK_FLAGGED            = "risk.flagged"

           
    DEPENDENCY_ADDED        = "dependency.added"
    DEPENDENCY_REMOVED      = "dependency.removed"

                   
    NOTIFICATION_SENT       = "notification.sent"
    ESCALATION_TRIGGERED    = "escalation.triggered"
    ESCALATION_RESOLVED     = "escalation.resolved"

               
    RELIABILITY_REFRESHED   = "analytics.reliability_refreshed"


                                                                     

@dataclass
class DomainEvent:
    event_id: uuid.UUID
    event_type: str
    org_id: uuid.UUID
    occurred_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, str]:
        event_data: dict[str, str] = {
            "event_id":    str(self.event_id),
            "event_type":  self.event_type,
            "org_id":      str(self.org_id),
            "occurred_at": self.occurred_at.isoformat(),
            "payload":     json.dumps(self.payload, default=str),
        }
        if self.correlation_id is not None:
            event_data["correlation_id"] = self.correlation_id
        return event_data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        payload = data.get("payload", "{}")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = payload

        return cls(
            event_id=uuid.UUID(data["event_id"]),
            event_type=data["event_type"],
            org_id=uuid.UUID(data["org_id"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
            payload=payload,
            correlation_id=data.get("correlation_id"),
        )

    @classmethod
    def create(
        cls,
        event_type: str,
        org_id: uuid.UUID,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> "DomainEvent":
        return cls(
            event_id=uuid.uuid4(),
            event_type=event_type,
            org_id=org_id,
            occurred_at=_now(),
            payload=payload,
            correlation_id=correlation_id,
        )
