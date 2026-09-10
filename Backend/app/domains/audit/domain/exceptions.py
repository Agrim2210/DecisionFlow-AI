from app.shared.exceptions import AppError, NotFoundError


class AuditWriteFailedError(AppError):
    status_code = 500
    error_code  = "AUDIT_WRITE_FAILED"
    message     = "Failed to write audit log. This is a critical error — check on-call."


class AuditLogNotFoundError(NotFoundError):
    error_code = "AUDIT_LOG_NOT_FOUND"
    message    = "Audit log entry not found"


class InvalidAuditEventError(AppError):
    status_code = 500
    error_code  = "INVALID_AUDIT_EVENT"
    message     = "Audit event type is malformed. Expected format: 'aggregate.action'"
