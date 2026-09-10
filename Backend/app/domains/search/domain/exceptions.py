from app.shared.exceptions import AppError, BadRequestError


class EmbeddingFailedError(AppError):
    status_code = 502
    error_code = "EMBEDDING_FAILED"
    message = "Failed to generate embeddings. The AI provider may be temporarily unavailable."


class SearchUnavailableError(AppError):
    status_code = 503
    error_code = "SEARCH_UNAVAILABLE"
    message = "Search is temporarily unavailable. Please try again shortly."


class InvalidSearchQueryError(BadRequestError):
    error_code = "INVALID_SEARCH_QUERY"
    message = "Search query is invalid or too short"


class InvalidSearchModeError(BadRequestError):
    error_code = "INVALID_SEARCH_MODE"
    message = "Invalid search mode. Valid: semantic, keyword, hybrid"


class IndexingFailedError(AppError):
    status_code = 500
    error_code = "INDEXING_FAILED"
    message = "Failed to index content into the search memory store"
