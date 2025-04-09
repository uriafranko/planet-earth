"""Configure Celery application for background tasks.

This module sets up the Celery application with appropriate configuration
for the planet-earth backend.
"""

from celery import Celery

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configure Celery
celery_app = Celery(
    "planet-earth",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Update Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=600,  # 10 minutes timeout for processing
    task_soft_time_limit=540,  # 9 minutes soft timeout
    result_expires=86400,  # Keep results for 1 day
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=150,
)

# Import tasks to ensure they're registered with Celery
# This needs to happen after the celery_app is created
if __name__ != "__main__":  # Avoid circular imports during execution
    from app.tasks import endpoints, schemas  # noqa: F401
