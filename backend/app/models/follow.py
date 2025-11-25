"""
Follow model for social connections.
"""

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Follow(Base):
    """
    Follow relationship model.
    
    Represents a directed follow relationship between users.
    User A follows User B means A will see B's posts in their feed.
    """
    __tablename__ = "follows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who is following whom
    follower_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], backref="following_relationships")
    following = relationship("User", foreign_keys=[following_id], backref="follower_relationships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id', name='unique_follow'),
        Index('idx_follower', 'follower_id'),
        Index('idx_following', 'following_id'),
    )
    
    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.following_id}>"

