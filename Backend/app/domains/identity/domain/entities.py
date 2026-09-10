   
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Organization:
       
    id: uuid.UUID
    name: str
    slug: str                                                         
    plan: str                                                      
    settings: dict                                                         
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def max_users(self) -> int:
        return {"starter": 10, "growth": 50, "business": 200, "enterprise": 99_999}.get(
            self.plan, 10
        )

    @property
    def max_meetings_per_month(self) -> int:
        return {"starter": 50, "growth": -1, "business": -1, "enterprise": -1}.get(
            self.plan, 50
        )                  

    @property
    def is_enterprise(self) -> bool:
        return self.plan == "enterprise"

    def can_add_user(self, current_user_count: int) -> bool:
        return current_user_count < self.max_users


@dataclass
class User:
       
    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    name: str
    hashed_password: str
    role: str                                                           
    is_active: bool = True
    is_email_verified: bool = False
    avatar_url: str | None = None
    email_verification_token: str | None = None
    email_verification_expires_at: datetime | None = None
    password_reset_token_hash: str | None = None
    password_reset_expires_at: datetime | None = None
    password_reset_used_at: datetime | None = None
    reliability_score: float = 100.0                                        
    last_active_at: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    deleted_at: datetime | None = None

                                                                   
    @property
    def is_owner(self) -> bool:
        return self.role == "owner"

    @property
    def is_admin_or_above(self) -> bool:
        return self.role in ("admin", "owner")

    @property
    def is_member_or_above(self) -> bool:
        return self.role in ("member", "admin", "owner")

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def can_manage_users(self) -> bool:
        return self.is_admin_or_above

    def can_view_all_analytics(self) -> bool:
        return self.is_admin_or_above

    def can_manage_billing(self) -> bool:
        return self.is_owner

    def can_manage_escalation_policies(self) -> bool:
        return self.is_admin_or_above


@dataclass
class PendingUser:
                                                                               
    id: uuid.UUID
    org_name: str | None
    org_slug: str | None
    email: str
    name: str
    hashed_password: str
    verification_token_hash: str
    verification_expires_at: datetime
    invited_org_id: uuid.UUID | None = None
    invited_role: str | None = None
    invited_by_user_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


@dataclass
class RefreshToken:
       
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str                                                  
    family_id: uuid.UUID                                            
    expires_at: datetime
    is_used: bool = False
    is_revoked: bool = False
    created_at: datetime = field(default_factory=_now)
    used_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    @property
    def is_valid(self) -> bool:
        return (
            not self.is_used
            and not self.is_revoked
            and self.expires_at > datetime.now(timezone.utc)
        )

    @property
    def is_expired(self) -> bool:
        return self.expires_at <= datetime.now(timezone.utc)
