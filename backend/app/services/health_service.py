"""
Health score service - calculates and manages user health scores.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.models.health_score import UserHealthScore
from app.services.tree_service import TreeService
from app.config import settings


class HealthService:
    """Service for calculating user health scores."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tree_service = TreeService(db)
    
    def calculate_health_score(self, user_id: UUID) -> float:
        """
        Calculate health score for a user based on their subtree.
        
        Health score formula:
        - Direct invitees: 50% weight
        - Level 2 descendants: 30% weight
        - Level 3+ descendants: 20% weight
        - Penalties for flagged (10 points) and banned (25 points)
        
        Args:
            user_id: UUID of user
            
        Returns:
            Health score (0-100)
        """
        descendants = self.tree_service.get_descendants(user_id, max_depth=None)
        
        if len(descendants) <= 1:  # Only the user themselves
            return 100.0
        
        # Separate by depth level
        level1 = [d for d in descendants if d["depth"] == 1]
        level2 = [d for d in descendants if d["depth"] == 2]
        level3_plus = [d for d in descendants if d["depth"] >= 3]
        
        # Calculate health for each level
        def level_health(users):
            if not users:
                return 100.0
            active = sum(1 for u in users if u["status"] == "active")
            return (active / len(users)) * 100
        
        level1_health = level_health(level1)
        level2_health = level_health(level2)
        level3_health = level_health(level3_plus)
        
        # Weighted average
        overall = (level1_health * 0.5) + (level2_health * 0.3) + (level3_health * 0.2)
        
        # Apply penalties
        flagged_count = sum(1 for d in descendants if d["status"] == "flagged")
        banned_count = sum(1 for d in descendants if d["status"] == "banned")
        
        penalty = (flagged_count * 10) + (banned_count * 25)
        
        final_score = max(0.0, min(100.0, overall - penalty))
        
        return round(final_score, 2)
    
    def determine_maturity_level(self, user: User, health_score: float) -> str:
        """
        Determine user's maturity level.
        
        Levels:
        - core: Core member (manually set)
        - supporting_trunk: Mature, healthy users who've grown a stable subtree
        - branch: Regular users
        
        Args:
            user: User object
            health_score: Current health score
            
        Returns:
            Maturity level string
        """
        if user.is_core_member:
            return "core"
        
        # Calculate account age
        account_age_days = (datetime.utcnow() - user.created_at).days
        
        # Get subtree stats
        stats = self.tree_service.get_subtree_stats(user.id)
        
        # Supporting trunk criteria
        if (
            account_age_days >= settings.SUPPORTING_TRUNK_MIN_DAYS
            and health_score >= settings.SUPPORTING_TRUNK_MIN_HEALTH
            and stats["max_depth"] >= settings.SUPPORTING_TRUNK_MIN_DEPTH
            and stats["total_descendants"] >= settings.SUPPORTING_TRUNK_MIN_SIZE
        ):
            return "supporting_trunk"
        
        return "branch"
    
    def calculate_and_store_health_score(self, user_id: UUID) -> UserHealthScore:
        """
        Calculate health score and store it in database.
        
        Args:
            user_id: UUID of user
            
        Returns:
            UserHealthScore object
        """
        user = self.tree_service.get_user_or_404(user_id)
        
        # Calculate health score
        health_score = self.calculate_health_score(user_id)
        
        # Get subtree stats
        stats = self.tree_service.get_subtree_stats(user_id)
        
        # Determine maturity
        maturity_level = self.determine_maturity_level(user, health_score)
        
        # Create health score record
        health_record = UserHealthScore(
            user_id=user_id,
            subtree_size=stats["total_descendants"],
            subtree_active_count=stats["active_count"],
            subtree_flagged_count=stats["flagged_count"],
            subtree_banned_count=stats["banned_count"],
            overall_health=health_score,
            max_depth_below=stats["max_depth"],
            maturity_level=maturity_level
        )
        
        self.db.add(health_record)
        self.db.commit()
        self.db.refresh(health_record)
        
        return health_record
    
    def get_latest_health_score(self, user_id: UUID) -> Optional[UserHealthScore]:
        """
        Get the most recent health score for a user.
        
        Args:
            user_id: UUID of user
            
        Returns:
            UserHealthScore object or None
        """
        return self.db.query(UserHealthScore).filter(
            UserHealthScore.user_id == user_id
        ).order_by(UserHealthScore.calculated_at.desc()).first()
    
    def calculate_all_health_scores(self) -> int:
        """
        Background task: Calculate health scores for all active users.
        
        Returns:
            Number of users processed
        """
        users = self.db.query(User).filter(
            User.deleted_at == None
        ).all()
        
        count = 0
        for user in users:
            try:
                self.calculate_and_store_health_score(user.id)
                count += 1
            except Exception as e:
                # Log error but continue processing
                print(f"Error calculating health score for user {user.id}: {e}")
                continue
        
        return count
    
    def flag_low_health_users(self, threshold: float = None) -> int:
        """
        Flag users with health scores below threshold.
        
        Args:
            threshold: Health score threshold (default from settings)
            
        Returns:
            Number of users flagged
        """
        if threshold is None:
            threshold = settings.HEALTH_SCORE_LOW_THRESHOLD
        
        # Get users with low health scores
        low_health_users = self.db.query(UserHealthScore).filter(
            UserHealthScore.overall_health < threshold,
            UserHealthScore.calculated_at >= datetime.utcnow() - timedelta(days=1)
        ).all()
        
        flagged_count = 0
        for health_record in low_health_users:
            user = self.db.query(User).filter(User.id == health_record.user_id).first()
            if user and user.status == "active":
                user.status = "flagged"
                flagged_count += 1
        
        if flagged_count > 0:
            self.db.commit()
        
        return flagged_count

