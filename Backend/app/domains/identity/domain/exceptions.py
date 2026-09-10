
   
from app.shared.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    PlanLimitExceededError,
    ValidationError,
)


                                                                    
class InvalidEmailError(ValidationError):
    error_code = "INVALID_EMAIL"
    message = "The provided email address is not valid"


class InvalidOrgSlugError(ValidationError):
    error_code = "INVALID_ORG_SLUG"
    message = "The organization slug is not valid"


class InvalidPasswordError(ValidationError):
    error_code = "INVALID_PASSWORD"
    message = "The password does not meet strength requirements"


class InvalidRoleError(ValidationError):
    error_code = "INVALID_ROLE"
    message = "The specified role is not valid"


                                                                     
class OrgNotFoundError(NotFoundError):
    error_code = "ORG_NOT_FOUND"
    message = "Organization not found"


class OrgSlugTakenError(ConflictError):
    error_code = "ORG_SLUG_TAKEN"
    message = "This organization slug is already taken. Please choose another."


class OrgUserLimitExceededError(PlanLimitExceededError):
    error_code = "ORG_USER_LIMIT_EXCEEDED"
    message = "Your plan's user limit has been reached. Please upgrade to add more members."


                                                                     
class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"
    message = "User not found"


class EmailAlreadyRegisteredError(ConflictError):
    error_code = "EMAIL_ALREADY_REGISTERED"
    message = "An account with this email address already exists"


class CannotChangeOwnerRoleError(PermissionDeniedError):
    error_code = "CANNOT_CHANGE_OWNER_ROLE"
    message = "The organization owner's role cannot be changed"


class CannotDeactivateSelfError(BadRequestError):
    error_code = "CANNOT_DEACTIVATE_SELF"
    message = "You cannot deactivate your own account"


class CannotDeactivateOwnerError(PermissionDeniedError):
    error_code = "CANNOT_DEACTIVATE_OWNER"
    message = "The organization owner cannot be deactivated"


                                                                     
class InvalidInviteTokenError(AuthenticationError):
    error_code = "INVALID_INVITE_TOKEN"
    message = "The invitation link is invalid or has expired"