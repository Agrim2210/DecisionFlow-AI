                                                    
from app.shared.exceptions import BadRequestError, NotFoundError


class NotificationNotFoundError(NotFoundError):
    error_code = "NOTIFICATION_NOT_FOUND"
    message = "Notification not found"


class EscalationNotFoundError(NotFoundError):
    error_code = "ESCALATION_NOT_FOUND"
    message = "Escalation not found"


class PolicyNotFoundError(NotFoundError):
    error_code = "ESCALATION_POLICY_NOT_FOUND"
    message = "Escalation policy not found"


class EscalationAlreadyResolvedError(BadRequestError):
    error_code = "ESCALATION_ALREADY_RESOLVED"
    message = "This escalation is already resolved or dismissed"


class EscalationMaxLevelError(BadRequestError):
    error_code = "ESCALATION_MAX_LEVEL"
    message = "Escalation has already reached the maximum level"


class NotificationDeliveryError(BadRequestError):
    error_code = "NOTIFICATION_DELIVERY_FAILED"
    message = "Failed to deliver notification"


class InvalidChannelError(BadRequestError):
    error_code = "INVALID_NOTIFICATION_CHANNEL"
    message = "Invalid notification channel specified"
