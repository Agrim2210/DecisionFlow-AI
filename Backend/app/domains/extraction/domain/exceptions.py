   
from app.shared.exceptions import (
    AppError,
    BadRequestError,
    NotFoundError,
)


class DecisionNotFoundError(NotFoundError):
    error_code = "DECISION_NOT_FOUND"
    message = "Decision not found"


class ActionItemNotFoundError(NotFoundError):
    error_code = "ACTION_ITEM_NOT_FOUND"
    message = "Action item not found"


class RiskNotFoundError(NotFoundError):
    error_code = "RISK_NOT_FOUND"
    message = "Risk not found"


class OpenQuestionNotFoundError(NotFoundError):
    error_code = "QUESTION_NOT_FOUND"
    message = "Open question not found"


class InvalidTaskTransitionError(BadRequestError):
    error_code = "INVALID_TASK_TRANSITION"
    message = "This status transition is not allowed for the current task state"


class PipelineStageError(AppError):
    status_code = 500
    error_code = "PIPELINE_STAGE_FAILED"
    message = "A pipeline stage failed during processing"


class AIExtractionError(AppError):
    status_code = 502
    error_code = "AI_EXTRACTION_FAILED"
    message = "AI extraction failed. The provider may be temporarily unavailable."


class EmbeddingError(AppError):
    status_code = 502
    error_code = "EMBEDDING_FAILED"
    message = "Failed to generate embeddings"


class OwnerResolutionError(AppError):
    status_code = 200                                                 
    error_code = "OWNER_NOT_RESOLVED"
    message = "Could not match speaker name to a known user"
