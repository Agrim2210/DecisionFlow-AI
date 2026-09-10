   
from app.shared.exceptions import BadRequestError, NotFoundError


class DependencyNotFoundError(NotFoundError):
    error_code = "DEPENDENCY_NOT_FOUND"
    message = "Dependency not found"


class CircularDependencyError(BadRequestError):
    error_code = "CIRCULAR_DEPENDENCY"
    message = "Adding this dependency would create a cycle in the task graph"


class SelfDependencyError(BadRequestError):
    error_code = "SELF_DEPENDENCY"
    message = "A task cannot depend on itself"


class DuplicateDependencyError(BadRequestError):
    error_code = "DUPLICATE_DEPENDENCY"
    message = "This dependency already exists"


class InvalidDependencyTypeError(BadRequestError):
    error_code = "INVALID_DEPENDENCY_TYPE"
    message = "Invalid dependency type. Valid: finish_to_start, start_to_start, finish_to_finish"
