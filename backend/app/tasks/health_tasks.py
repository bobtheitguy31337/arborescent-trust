"""
Background tasks for health score calculation.
"""

from celery import Task
from datetime import datetime

from app.tasks import celery_app
from app.database import SessionLocal
from app.services.health_service import HealthService
from app.models.user import User


class DatabaseTask(Task):
    """Base task with database session."""
    
    def __call__(self, *args, **kwargs):
        db = SessionLocal()
        try:
            return self.run(*args, db=db, **kwargs)
        finally:
            db.close()


@celery_app.task(base=DatabaseTask, name="tasks.calculate_all_health_scores")
def calculate_all_health_scores(db=None):
    """
    Calculate health scores for all active users.
    
    Runs daily.
    """
    health_service = HealthService(db)
    
    processed_count = health_service.calculate_all_health_scores()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "processed_count": processed_count,
        "status": "completed"
    }


@celery_app.task(base=DatabaseTask, name="tasks.flag_low_health_users")
def flag_low_health_users(db=None, threshold=None):
    """
    Flag users with health scores below threshold.
    
    Runs daily after health score calculation.
    """
    health_service = HealthService(db)
    
    flagged_count = health_service.flag_low_health_users(threshold)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "flagged_count": flagged_count,
        "status": "completed"
    }


@celery_app.task(base=DatabaseTask, name="tasks.adjust_invite_quotas")
def adjust_invite_quotas(db=None):
    """
    Grant additional invite capacity to healthy, mature users.
    
    Runs daily.
    """
    from app.models.audit_log import InviteAuditLog
    from app.config import settings
    
    # Get users eligible for quota increase
    users = db.query(User).filter(
        User.deleted_at == None,
        User.status == "active",
        User.invites_available < 3  # Only adjust if running low
    ).all()
    
    adjusted_count = 0
    for user in users:
        # Simple logic: grant 1 additional invite per month of good standing
        # In production, this would be more sophisticated
        account_age_days = (datetime.utcnow() - user.created_at).days
        
        if account_age_days >= 30 and user.invite_quota < 50:
            additional = 1
            old_quota = user.invite_quota
            user.invite_quota += additional
            
            # Log to audit
            audit_entry = InviteAuditLog(
                event_type="quota_adjusted",
                actor_user_id=None,
                target_user_id=user.id,
                event_data={
                    "old_quota": old_quota,
                    "new_quota": user.invite_quota,
                    "reason": "Automatic quota increase - good standing"
                }
            )
            db.add(audit_entry)
            adjusted_count += 1
    
    if adjusted_count > 0:
        db.commit()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "adjusted_count": adjusted_count,
        "status": "completed"
    }


# Add to beat schedule
celery_app.conf.beat_schedule.update({
    "calculate-health-daily": {
        "task": "tasks.calculate_all_health_scores",
        "schedule": 86400.0,  # Every 24 hours
    },
    "flag-low-health-daily": {
        "task": "tasks.flag_low_health_users",
        "schedule": 86400.0,  # Every 24 hours
    },
    "adjust-quotas-daily": {
        "task": "tasks.adjust_invite_quotas",
        "schedule": 86400.0,  # Every 24 hours
    },
})

