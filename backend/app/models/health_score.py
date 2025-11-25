"""
User Health Score model - Calculated periodically to assess invite tree quality.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class UserHealthScore(Base):
    """
    Health score snapshot for a user at a point in time.
    
    Calculated daily via background task. Tracks:
    - Subtree size and composition
    - Health metrics (active vs flagged/banned)
    - Maturity level
    """
    
    __tablename__ = "user_health_scores"
    
    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # User reference
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Subtree statistics
    subtree_size = Column(Integer, default=0)
    subtree_active_count = Column(Integer, default=0)
    subtree_flagged_count = Column(Integer, default=0)
    subtree_banned_count = Column(Integer, default=0)
    
    # Health scores (0-100)
    direct_invitee_health = Column(Numeric(5, 2), default=100.0)
    subtree_health = Column(Numeric(5, 2), default=100.0)
    overall_health = Column(Numeric(5, 2), default=100.0, index=True)
    
    # Tree metrics
    max_depth_below = Column(Integer, default=0)
    
    # Maturity classification
    maturity_level = Column(String(20), default="branch")  # branch, supporting_trunk, core
    
    # Calculation timestamp
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<UserHealthScore(user_id={self.user_id}, overall_health={self.overall_health}, calculated_at={self.calculated_at})>"

