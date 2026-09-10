   
from app.shared.exceptions import BadRequestError, ConflictError, NotFoundError


class MeetingNotFoundError(NotFoundError):
    error_code = "MEETING_NOT_FOUND"
    message = "Meeting not found"


class TranscriptNotFoundError(NotFoundError):
    error_code = "TRANSCRIPT_NOT_FOUND"
    message = "Transcript not found for this meeting"


class DuplicateTranscriptError(ConflictError):
    error_code = "DUPLICATE_TRANSCRIPT"
    message = "This transcript has already been uploaded"


class InvalidFileTypeError(BadRequestError):
    error_code = "INVALID_FILE_TYPE"
    message = "Unsupported file type. Accepted: .txt, .vtt, .srt, .docx, .md"


class FileTooLargeError(BadRequestError):
    error_code = "FILE_TOO_LARGE"
    message = "File exceeds the maximum allowed size of 50MB"


class InvalidStatusTransitionError(BadRequestError):
    error_code = "INVALID_STATUS_TRANSITION"
    message = "This status transition is not allowed"


class ProcessingFailedError(BadRequestError):
    error_code = "PROCESSING_FAILED"
    message = "Meeting processing failed. Please try again."
