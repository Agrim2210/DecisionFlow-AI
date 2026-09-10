   
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class UserRegistered:
                                                                    
    event_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    email: str
    org_name: str
    org_slug: str
    plan: str
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        email: str,
        org_name: str,
        org_slug: str,
        plan: str,
    ) -> "UserRegistered":
        return cls(
            event_id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            email=email,
            org_name=org_name,
            org_slug=org_slug,
            plan=plan,
            occurred_at=_now(),
        )


@dataclass(frozen=True)
class UserLoggedIn:
                                                                                        
    event_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    ip_address: str | None
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
    ) -> "UserLoggedIn":
        return cls(
            event_id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            ip_address=ip_address,
            occurred_at=_now(),
        )


@dataclass(frozen=True)
class UserInvited:
                                                                
    event_id: uuid.UUID
    org_id: uuid.UUID
    invited_user_id: uuid.UUID
    invited_email: str
    invited_role: str
    invited_by_user_id: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        invited_user_id: uuid.UUID,
        invited_email: str,
        invited_role: str,
        invited_by_user_id: uuid.UUID,
    ) -> "UserInvited":
        return cls(
            event_id=uuid.uuid4(),
            org_id=org_id,
            invited_user_id=invited_user_id,
            invited_email=invited_email,
            invited_role=invited_role,
            invited_by_user_id=invited_by_user_id,
            occurred_at=_now(),
        )


@dataclass(frozen=True)
class RoleChanged:
                                                            
    event_id: uuid.UUID
    org_id: uuid.UUID
    target_user_id: uuid.UUID
    old_role: str
    new_role: str
    changed_by_user_id: uuid.UUID
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        old_role: str,
        new_role: str,
        changed_by_user_id: uuid.UUID,
    ) -> "RoleChanged":
        return cls(
            event_id=uuid.uuid4(),
            org_id=org_id,
            target_user_id=target_user_id,
            old_role=old_role,
            new_role=new_role,
            changed_by_user_id=changed_by_user_id,
            occurred_at=_now(),
        )


@dataclass(frozen=True)
class TokenReuseDetected:
       
    event_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    family_id: uuid.UUID
    ip_address: str | None
    occurred_at: datetime

    @classmethod
    def create(
        cls,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        family_id: uuid.UUID,
        ip_address: str | None,
    ) -> "TokenReuseDetected":
        return cls(
            event_id=uuid.uuid4(),
            org_id=org_id,
            user_id=user_id,
            family_id=family_id,
            ip_address=ip_address,
            occurred_at=_now(),
        )