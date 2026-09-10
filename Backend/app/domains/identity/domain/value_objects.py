
   
from __future__ import annotations

import re
from dataclasses import dataclass

from app.domains.identity.domain.exceptions import (
    InvalidEmailError,
    InvalidOrgSlugError,
    InvalidPasswordError,
    InvalidRoleError,
)

_VALID_PLANS = frozenset({"starter", "growth", "business", "enterprise"})
_VALID_ROLES = frozenset({"viewer", "member", "admin", "owner"})
_SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]{1,98}[a-z0-9]$")
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.lower().strip()
        object.__setattr__(self, "value", normalized)
        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError(f"'{self.value}' is not a valid email address")
        if len(normalized) > 255:
            raise InvalidEmailError("Email address is too long (max 255 characters)")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class OrgSlug:
    value: str

    def __post_init__(self) -> None:
        slug = self.value.lower().strip()
        object.__setattr__(self, "value", slug)
        if not _SLUG_PATTERN.match(slug):
            raise InvalidOrgSlugError(
                f"'{self.value}' is not a valid org slug. "
                "Use 2-100 lowercase letters, numbers, and hyphens. "
                "Must start and end with alphanumeric."
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Role:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_ROLES:
            raise InvalidRoleError(
                f"'{self.value}' is not a valid role. Valid: {sorted(_VALID_ROLES)}"
            )

    @property
    def level(self) -> int:
        return {"viewer": 0, "member": 1, "admin": 2, "owner": 3}[self.value]

    def is_at_least(self, minimum: str) -> bool:
        minimum_level = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}.get(minimum, -1)
        return self.level >= minimum_level

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Plan:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_PLANS:
            raise ValueError(f"'{self.value}' is not a valid plan. Valid: {sorted(_VALID_PLANS)}")

    def __str__(self) -> str:
        return self.value


class PasswordPolicy:
    
    MIN_LENGTH = 8
    MAX_LENGTH = 128

    @classmethod
    def validate(cls, password: str) -> str:


           
        errors: list[str] = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"at least {cls.MIN_LENGTH} characters")
        if len(password) > cls.MAX_LENGTH:
            errors.append(f"no more than {cls.MAX_LENGTH} characters")
        if not re.search(r"[A-Z]", password):
            errors.append("at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            errors.append("at least one lowercase letter")
        if not re.search(r"\d", password):
            errors.append("at least one digit")

        if errors:
            raise InvalidPasswordError(
                f"Password must contain: {', '.join(errors)}"
            )
        return password