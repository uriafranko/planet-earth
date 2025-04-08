#!/bin/bash
set -e

# Use environment variable SERVICE_TYPE with "api" as default
SERVICE_TYPE=${SERVICE_TYPE:-api}

# Ensure the virtual environment is activated
source /app/.venv/bin/activate

echo "Starting service: $SERVICE_TYPE"

case "$SERVICE_TYPE" in
  "api" | "web" | "server")
    echo "Starting FastAPI server..."
    # Use direct path to uvicorn in virtual environment
    exec /app/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  "worker" | "celery")
    echo "Starting Celery worker..."
    # Use direct path to celery in virtual environment
    exec /app/.venv/bin/celery -A app.tasks.celery_app worker --loglevel=INFO
    ;;
  *)
    echo "Unknown service type: $SERVICE_TYPE"
    echo "Valid options: api, web, server, worker, celery"
    exit 1
    ;;
esac
