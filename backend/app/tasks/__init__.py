"""
Celery background tasks.
"""

from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "arborescent_trust",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks to register them
from app.tasks import invite_tasks, health_tasks

__all__ = ["celery_app"]

