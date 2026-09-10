   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GetMeQuery:
                                                             
    user_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class GetUserQuery:
                                                          
    user_id: uuid.UUID
    org_id: uuid.UUID


@dataclass(frozen=True)
class ListUsersQuery:
                                                                   
    org_id: uuid.UUID
    limit: int = 50
    cursor_id: uuid.UUID | None = None
    role_filter: str | None = None                                   
    active_only: bool = True


@dataclass(frozen=True)
class GetOrgQuery:
                            
    org_id: uuid.UUID
