"""
Notification model for user alerts.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications."""
    LIKE = "like"
    REPOST = "repost"
    REPLY = "reply"
    FOLLOW = "follow"
    MENTION = "mention"
    INVITE_USED = "invite_used"
    TRUST_CHANGE = "trust_change"


class Notification(Base):
    """
    Notification model.
    
    Alerts users to activity related to their account:
    - Likes, reposts, replies on their posts
    - New followers
    - Mentions
    - Invite system events
    """
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who receives this notification
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Who triggered it (nullable for system notifications)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Notification details
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    
    # Related entities (all nullable, depends on type)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    
    # Message/context
    message = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)  # Extra data as needed (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Status
    read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="notifications")
    actor = relationship("User", foreign_keys=[actor_id])
    post = relationship("Post", foreign_keys=[post_id])
    
    def __repr__(self):
        return f"<Notification {self.notification_type} for {self.user_id}>"

