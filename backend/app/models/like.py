"""
Like model for post interactions.
"""

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Like(Base):
    """
    Like model for posts.
    
    Represents a user liking a post.
    """
    __tablename__ = "likes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="likes")
    post = relationship("Post", back_populates="likes")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'post_id', name='unique_like'),
        Index('idx_like_user', 'user_id'),
        Index('idx_like_post', 'post_id'),
    )
    
    def __repr__(self):
        return f"<Like {self.user_id} -> Post {self.post_id}>"

