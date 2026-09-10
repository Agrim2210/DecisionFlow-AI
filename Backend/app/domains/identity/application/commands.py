   
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterOrgCommand:
                                                             
    org_name: str
    org_slug: str
    user_name: str
    email: str                                                               
    password: str                                                 
    ip_address: str | None = None


@dataclass(frozen=True)
class LoginCommand:
                                                    
    email: str                              
    password: str
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class RequestPasswordResetCommand:
    email: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    raw_token: str
    new_password: str


@dataclass(frozen=True)
class RefreshTokensCommand:
                                                              
    raw_refresh_token: str
    ip_address: str | None = None


@dataclass(frozen=True)
class LogoutCommand:
                                                                
    user_id: uuid.UUID
    raw_refresh_token: str | None = None                               
    logout_all: bool = False


@dataclass(frozen=True)
class InviteUserCommand:
                                                  
    org_id: uuid.UUID
    invited_by_user_id: uuid.UUID
    email: str
    name: str
    role: str                                            
    temp_password: str                                                            


@dataclass(frozen=True)
class UpdateProfileCommand:
                                          
    user_id: uuid.UUID
    org_id: uuid.UUID
    name: str | None = None
    avatar_url: str | None = None


@dataclass(frozen=True)
class ChangePasswordCommand:
                                           
    user_id: uuid.UUID
    org_id: uuid.UUID
    current_password: str
    new_password: str


@dataclass(frozen=True)
class ChangeUserRoleCommand:
                                             
    org_id: uuid.UUID
    target_user_id: uuid.UUID
    new_role: str
    changed_by_user_id: uuid.UUID


@dataclass(frozen=True)
class DeactivateUserCommand:
                                            
    org_id: uuid.UUID
    target_user_id: uuid.UUID
    requested_by_user_id: uuid.UUID


@dataclass(frozen=True)
class UpdateOrgSettingsCommand:
                                               
    org_id: uuid.UUID
    requested_by_user_id: uuid.UUID
    name: str | None = None
    settings: dict | None = None
