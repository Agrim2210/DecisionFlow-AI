   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DependencyAdded:
                                                                          
    event_id: uuid.UUID
    org_id: uuid.UUID
    dependency_id: uuid.UUID
    upstream_id: uuid.UUID
    downstream_id: uuid.UUID
    dependency_type: str
    detected_by: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        dependency_id: uuid.UUID,
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
        dependency_type: str,
        detected_by: str,
    ) -> "DependencyAdded":
        return cls(
            event_id=uuid.uuid4(), org_id=org_id, dependency_id=dependency_id,
            upstream_id=upstream_id, downstream_id=downstream_id,
            dependency_type=dependency_type, detected_by=detected_by,
            occurred_at=_now(),
        )


@dataclass(frozen=True)
class DependencyRemoved:
                                                    
    event_id: uuid.UUID
    org_id: uuid.UUID
    dependency_id: uuid.UUID
    removed_by: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(cls, org_id: uuid.UUID, dependency_id: uuid.UUID, removed_by: uuid.UUID) -> "DependencyRemoved":
        return cls(
            event_id=uuid.uuid4(), org_id=org_id, dependency_id=dependency_id,
            removed_by=removed_by, occurred_at=_now(),
        )


@dataclass(frozen=True)
class CycleDetected:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    upstream_id: uuid.UUID
    downstream_id: uuid.UUID
    cycle_path: list[str]                                           
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        upstream_id: uuid.UUID,
        downstream_id: uuid.UUID,
        cycle_path: list[str],
    ) -> "CycleDetected":
        return cls(
            event_id=uuid.uuid4(), org_id=org_id, upstream_id=upstream_id,
            downstream_id=downstream_id, cycle_path=cycle_path, occurred_at=_now(),
        )
