from celery import Celery
from app.shared.config import settings

celery_app = Celery(
    "decisionflow",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.shared.workers.pipeline_tasks",
        "app.shared.workers.escalation_tasks",
        "app.shared.workers.analytics_tasks",
        "app.shared.workers.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.shared.workers.pipeline_tasks.*":    {"queue": "pipeline"},
        "app.shared.workers.escalation_tasks.*":  {"queue": "escalation"},
        "app.shared.workers.analytics_tasks.*":   {"queue": "analytics"},
        "app.shared.workers.notification_tasks.*":{"queue": "notifications"},
    },
    beat_schedule={
        "scan-overdue-tasks": {
            "task": "app.shared.workers.escalation_tasks.scan_overdue_tasks",
            "schedule": 360.0,
        },
        "advance-escalations": {
            "task": "app.shared.workers.escalation_tasks.advance_escalations",
            "schedule": 3600.0,
        },
        "refresh-reliability": {
            "task": "app.shared.workers.analytics_tasks.refresh_all_reliability",
            "schedule": 3600.0,
        },
        "refresh-execution-rates": {
            "task": "app.shared.workers.analytics_tasks.refresh_execution_rates",
            "schedule": 300.0,       # every 5 minutes
        },
        "retry-incomplete-pipelines": {
            "task": "app.shared.workers.pipeline_tasks.retry_incomplete_pipelines",
            "schedule": 120.0,       # every 2 minutes
        },
    },
)
