#!/bin/bash
set -e

# Default to "api" if no argument is provided
SERVICE_TYPE=${1:-api}

echo "Starting service: $SERVICE_TYPE"

case "$SERVICE_TYPE" in
  "api" | "web" | "server")
    echo "Starting FastAPI server..."
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
    ;;
  "worker" | "celery")
    echo "Starting Celery worker..."
    exec python -m celery -A app.tasks.celery_app worker --loglevel=INFO
    ;;
  *)
    echo "Unknown service type: $SERVICE_TYPE"
    echo "Valid options: api, web, server, worker, celery"
    exit 1
    ;;
esac
