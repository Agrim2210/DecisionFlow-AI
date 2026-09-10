
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.shared.config import settings

_pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    bcrypt__rounds=12,
)


_DUMMY_HASH = _pwd_context.hash("__dummy_password_for_timing_safety__")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str | None) -> bool:
   
    return _pwd_context.verify(plain, hashed or _DUMMY_HASH)


def get_dummy_hash() -> str:
    return _DUMMY_HASH


def create_access_token(
    *,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    role: str,
    plan: str,
) -> str:
       
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "role": role,
        "plan": plan,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
       
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "org_id", "role", "exp", "type", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Token type must be 'access'")
    return payload


                                                                    
def generate_refresh_token() -> tuple[str, str]:
       
    raw = secrets.token_urlsafe(64)                        
    hashed = _hash_refresh_token(raw)
    return raw, hashed


def _hash_refresh_token(raw: str) -> str:
                                                           
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_refresh_token(raw: str) -> str:
                                                                                  
    return _hash_refresh_token(raw)


def refresh_token_expiry() -> datetime:
                                                                   
    return datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)


def generate_email_verification_token() -> tuple[str, str]:
                                                                              
    return generate_one_time_token()


def hash_email_verification_token(raw: str) -> str:
                                                                                       
    return hash_one_time_token(raw)


def email_verification_expiry() -> datetime:
    return one_time_token_expiry(settings.EMAIL_VERIFICATION_TTL_MINUTES)


def invitation_token_expiry() -> datetime:
    """Invitation links get a much longer TTL (default 72 hours)."""
    return datetime.now(timezone.utc) + timedelta(hours=settings.INVITATION_TTL_HOURS)


def generate_one_time_token() -> tuple[str, str]:
                                                                                  
    raw = secrets.token_urlsafe(48)
    return raw, hash_one_time_token(raw)


def hash_one_time_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def one_time_token_expiry(ttl_minutes: int) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)


                                                                    
def extract_bearer_token(authorization: str | None) -> str | None:
       
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token if token else None
