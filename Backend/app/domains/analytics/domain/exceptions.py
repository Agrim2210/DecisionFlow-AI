   
from app.shared.exceptions import AppError, NotFoundError


class InsufficientDataError(AppError):
    status_code = 200                                                   
    error_code = "INSUFFICIENT_DATA"
    message = "Not enough data to compute analytics. Assign and complete tasks to see scores."


class SnapshotStaleError(AppError):
    status_code = 200
    error_code = "SNAPSHOT_STALE"
    message = "Analytics snapshot is stale. A refresh is scheduled within the hour."


class InvalidScoreError(AppError):
    status_code = 500
    error_code = "INVALID_SCORE"
    message = "Computed score is out of valid range — this is a bug"


class MeetingAnalyticsNotFoundError(NotFoundError):
    error_code = "MEETING_ANALYTICS_NOT_FOUND"
    message = "Analytics not yet available for this meeting. Run the pipeline first."


class SnapshotNotFoundError(NotFoundError):
    error_code = "SNAPSHOT_NOT_FOUND"
    message = "No reliability snapshot found for this user"
