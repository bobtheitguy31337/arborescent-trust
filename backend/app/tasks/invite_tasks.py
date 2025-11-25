"""
Background tasks for invite token management.
"""

from celery import Task
from datetime import datetime

from app.tasks import celery_app
from app.database import SessionLocal
from app.services.invite_service import InviteService


class DatabaseTask(Task):
    """Base task with database session."""
    
    def __call__(self, *args, **kwargs):
        db = SessionLocal()
        try:
            return self.run(*args, db=db, **kwargs)
        finally:
            db.close()


@celery_app.task(base=DatabaseTask, name="tasks.expire_unused_tokens")
def expire_unused_tokens(db=None):
    """
    Expire unused invite tokens and credit back to creators.
    
    Runs every hour.
    """
    invite_service = InviteService(db)
    
    expired_count = invite_service.expire_unused_tokens()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "expired_count": expired_count,
        "status": "completed"
    }


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "expire-tokens-hourly": {
        "task": "tasks.expire_unused_tokens",
        "schedule": 3600.0,  # Every hour
    },
}

