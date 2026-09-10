   
from __future__ import annotations

import re
import uuid
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


                                                 
                 
                                                 

class RegisterRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=255, examples=["Acme Corp"])
    org_slug: str = Field(
        ...,
        min_length=2,
        max_length=100,
        pattern=r"^[a-z0-9][a-z0-9\-]{0,98}[a-z0-9]$",
        examples=["acme-corp"],
        description="Lowercase letters, numbers, hyphens. Must start/end with alphanumeric.",
    )
    name: str = Field(..., min_length=1, max_length=255, examples=["Rahul Sharma"])
    email: EmailStr = Field(..., examples=["rahul@acme.com"])
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("org_slug", mode="before")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("org_name", "name", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequestResponse(BaseModel):
    message: str


class RefreshRequest(BaseModel):
       
    refresh_token: str | None = Field(
        default=None,
        description="Refresh token. Prefer sending via HttpOnly cookie.",
    )


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    logout_all: bool = Field(
        default=False,
        description="Revoke all sessions for this user (not just current device)",
    )


class InviteUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., pattern=r"^(viewer|member|admin)$")
    temp_password: str = Field(
        ..., min_length=8, max_length=128,
        description="Initial password set by the admin; the invitee replaces it after verification.",
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class ChangeRoleRequest(BaseModel):
    role: str = Field(..., pattern=r"^(viewer|member|admin)$")


class UpdateProfileRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=1000)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_must_differ(self) -> "ChangePasswordRequest":
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current password")
        return self


class UpdateOrgSettingsRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Partial update — merged with existing settings",
    )


class ListUsersRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None
    role: str | None = Field(default=None, pattern=r"^(viewer|member|admin|owner)$")


                                                 
                  
                                                 

class TokenResponse(BaseModel):
       
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until access token expires")


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    max_users: int
    settings: dict[str, Any]
    created_at: str                      

    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    name: str
    role: str
    avatar_url: str | None
    is_active: bool
    is_email_verified: bool
    reliability_score: float
    last_active_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
                                         
    user: UserResponse
    organization: OrgResponse
    tokens: TokenResponse


class RegistrationPendingResponse(BaseModel):
    message: str
    email: EmailStr
    verification_url: str | None = None


class RefreshResponse(BaseModel):
    tokens: TokenResponse


class MeResponse(BaseModel):
    user: UserResponse
    organization: OrgResponse


class PendingUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    invited_role: str
    verification_expires_at: str
    created_at: str

    model_config = {"from_attributes": True}


class PendingUserListResponse(BaseModel):
    invitations: list[PendingUserResponse]


class UserListResponse(BaseModel):
    users: list[UserResponse]
    has_next: bool
    next_cursor: str | None
    total: int | None = None


                                                 
                                           
                                                                     
                                                 

def map_user_to_response(user: Any) -> UserResponse:
    from app.shared.config import settings as cfg
    return UserResponse(
        id=user.id,
        org_id=user.org_id,
        email=user.email,
        name=user.name,
        role=user.role,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_email_verified=user.is_email_verified,
        reliability_score=float(user.reliability_score),
        last_active_at=user.last_active_at.isoformat() if user.last_active_at else None,
        created_at=user.created_at.isoformat(),
    )


def map_org_to_response(org: Any) -> OrgResponse:
    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        plan=org.plan,
        max_users=org.max_users,
        settings=org.settings or {},
        created_at=org.created_at.isoformat(),
    )


def make_token_response(access_token: str) -> TokenResponse:
    from app.shared.config import settings as cfg
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=cfg.access_token_expire_seconds,
    )
