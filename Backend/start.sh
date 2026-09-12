#!/bin/bash
set -e

echo "=== DecisionFlow AI Starting ==="

# Wait for and apply database migrations
if [ -n "$DATABASE_URL" ]; then
    echo "Applying database migrations via Alembic..."
    alembic -c alembic.ini upgrade head || {
        echo "Alembic migration failed on first attempt, waiting 3 seconds to retry..."
        sleep 3
        alembic -c alembic.ini upgrade head
    }
fi

# Manage Redis
# If no REDIS_URL is provided, or if it points to localhost/127.0.0.1, start local redis-server
if [ -z "$REDIS_URL" ] || [[ "$REDIS_URL" == *"localhost"* ]] || [[ "$REDIS_URL" == *"127.0.0.1"* ]]; then
    echo "Starting embedded Redis daemon..."
    redis-server --daemonize yes
    export REDIS_URL="redis://127.0.0.1:6379/0"
    export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://127.0.0.1:6379/1}"
    export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://127.0.0.1:6379/2}"
fi

# Start Celery worker & beat inside the container unless explicitly disabled
if [ "$RUN_WORKER_IN_CONTAINER" != "false" ]; then
    echo "Starting Celery worker in background..."
    celery -A app.shared.workers.celery_app.celery_app worker --loglevel=info --concurrency=2 -Q pipeline,escalation,analytics,notifications,celery &
    
    echo "Starting Celery beat in background..."
    celery -A app.shared.workers.celery_app.celery_app beat --loglevel=info &
fi

PORT="${PORT:-8000}"
echo "Starting Uvicorn on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 2