"""Tasks package for asynchronous processing with Celery.

This package contains all Celery tasks used for background processing
in the planet-earth application.
"""

# Import core task modules for easy access
from app.tasks import documents, endpoints, schemas

# Export Celery app for use in other modules
from app.tasks.celery_app import celery_app

__all__ = ["celery_app", "documents", "endpoints", "schemas"]
