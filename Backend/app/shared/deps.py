   
from __future__ import annotations

import uuid
from typing import Annotated

import jwt
import structlog
from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import get_db, set_tenant_context
from app.shared.exceptions import (
    AuthenticationError,
    InsufficientRoleError,
    InvalidTokenError,
    TokenExpiredError,
    UserInactiveError,
)
from app.shared.security import decode_access_token

logger = structlog.get_logger(__name__)

                                                                       
_bearer = HTTPBearer(auto_error=False)

                                                
_ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 0,
    "member": 1,
    "admin": 2,
    "owner": 3,
}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> "User":                                            
       
    from app.domains.identity.infra.orm_models import UserORM

    if not credentials:
        raise AuthenticationError("Authorization header with Bearer token is required")

                        
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except jwt.PyJWTError as exc:
        logger.debug("jwt_decode_failed", error=str(exc))
        raise InvalidTokenError()

                          
    try:
        user_id = uuid.UUID(payload["sub"])
        org_id = uuid.UUID(payload["org_id"])
    except (KeyError, ValueError):
        raise InvalidTokenError("Token contains invalid UUID claims")

                                                                   
    result = await db.execute(
        select(UserORM).where(
            UserORM.id == user_id,
            UserORM.org_id == org_id,
            UserORM.deleted_at.is_(None),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthenticationError("User associated with this token no longer exists")

    if not user.is_active:
        raise UserInactiveError()

                                        
    await set_tenant_context(db, org_id)

    return user


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> "User | None":                                            
       
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except Exception:
        return None


def require_role(minimum_role: str):
       
    if minimum_role not in _ROLE_HIERARCHY:
        raise ValueError(f"Unknown role: {minimum_role!r}. Valid: {list(_ROLE_HIERARCHY)}")

    min_level = _ROLE_HIERARCHY[minimum_role]

    async def _dependency(
        current_user: Annotated["User", Depends(get_current_user)],                                            
    ) -> "User":                                            
        user_level = _ROLE_HIERARCHY.get(current_user.role, -1)
        if user_level < min_level:
            raise InsufficientRoleError(
                f"This action requires '{minimum_role}' role or above. "
                f"Your role is '{current_user.role}'."
            )
        return current_user

    _dependency.__name__ = f"require_{minimum_role}"
    return _dependency


                                                                    
                                                                                 

require_viewer = require_role("viewer")                           
require_member = require_role("member")                         
require_admin = require_role("admin")                   
require_owner = require_role("owner")                 


                                                                    
                                                

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated["User", Depends(get_current_user)]                                                    
MemberUser = Annotated["User", Depends(require_member)]                                                       
AdminUser = Annotated["User", Depends(require_admin)]                                                         
OwnerUser = Annotated["User", Depends(require_owner)]                                                         