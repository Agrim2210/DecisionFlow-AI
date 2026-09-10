   
from __future__ import annotations

from typing import Any


class AppError(Exception):
                                                          

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
        **context: Any,
    ) -> None:
        self.message = message or self.__class__.message
        if error_code:
            self.error_code = error_code
        self.context = context
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code}, message={self.message!r})"


                                                                    
class BadRequestError(AppError):
    status_code = 400
    error_code = "BAD_REQUEST"
    message = "Invalid request"


class ValidationError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Request validation failed"


                                                                    
class AuthenticationError(AppError):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication required"


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    message = "Your session has expired. Please log in again."


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    message = "Token is invalid or malformed"


class TokenRevokedError(AuthenticationError):
    error_code = "TOKEN_REVOKED"
    message = "This token has been revoked"


class RefreshTokenReuseError(AuthenticationError):
       
    error_code = "TOKEN_REUSE_DETECTED"
    message = (
        "A security issue was detected with your session. "
        "All sessions have been revoked. Please log in again."
    )


                                                                    
class PermissionDeniedError(AppError):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action"


class InsufficientRoleError(PermissionDeniedError):
    error_code = "INSUFFICIENT_ROLE"
    message = "Your role does not permit this action"


class EmailNotVerifiedError(PermissionDeniedError):
    error_code = "EMAIL_NOT_VERIFIED"
    message = "Please verify your email address to continue"


class UserInactiveError(PermissionDeniedError):
    error_code = "USER_INACTIVE"
    message = "Your account has been deactivated. Contact your administrator."


                                                                    
class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found"


                                                                   
class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"
    message = "A conflict occurred with the current state of the resource"


class DuplicateError(ConflictError):
    error_code = "DUPLICATE_RESOURCE"
    message = "This resource already exists"


                                                                    
class PlanLimitExceededError(AppError):
    status_code = 402
    error_code = "PLAN_LIMIT_EXCEEDED"
    message = "You have reached the limit for your current plan. Please upgrade."


                                                                    
class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please wait before trying again."


                                                                    
class ExternalServiceError(AppError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "An upstream service is temporarily unavailable"


class AIProviderError(ExternalServiceError):
    error_code = "AI_PROVIDER_ERROR"
    message = "The AI provider is temporarily unavailable. Please try again."


                                                                    
class InternalError(AppError):
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An unexpected error occurred"


class PipelineError(InternalError):
    error_code = "PIPELINE_ERROR"
    message = "Processing pipeline encountered an error"


class AuditWriteError(InternalError):
       
    error_code = "AUDIT_WRITE_FAILED"
    message = "Failed to write audit log"