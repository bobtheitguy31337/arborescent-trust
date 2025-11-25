"""
Post model for social media functionality.
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class PostVisibility(str, enum.Enum):
    """Post visibility options."""
    PUBLIC = "public"
    FOLLOWERS = "followers"
    MENTIONED = "mentioned"


class Post(Base):
    """
    Post model - represents a user's post/tweet.
    
    Features:
    - Text content (max 280 chars for tweet-like behavior)
    - Media attachments (images, videos, gifs)
    - Reply threading
    - Visibility controls
    """
    __tablename__ = "posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)  # Max 280 enforced at API level
    
    # Reply threading
    reply_to_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    reply_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_reply = Column(Boolean, default=False, index=True)
    
    # Repost reference
    repost_of_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    is_repost = Column(Boolean, default=False, index=True)
    
    # Visibility
    visibility = Column(Enum(PostVisibility), default=PostVisibility.PUBLIC, nullable=False)
    
    # Engagement counters (denormalized for performance)
    like_count = Column(Integer, default=0)
    repost_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    author = relationship("User", foreign_keys=[user_id], back_populates="posts")
    media = relationship("Media", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")
    reposts = relationship("Post", 
                          foreign_keys=[repost_of_id],
                          remote_side=[id],
                          backref="reposted_by")
    replies = relationship("Post",
                          foreign_keys=[reply_to_id],
                          remote_side=[id],
                          backref="parent_post")
    
    def __repr__(self):
        return f"<Post {self.id} by {self.user_id}>"


class Media(Base):
    """
    Media attachments for posts.
    
    Supports:
    - Images (JPG, PNG, GIF)
    - Videos (MP4, MOV)
    - GIFs
    """
    __tablename__ = "media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Media info
    media_type = Column(String(20), nullable=False)  # image, video, gif
    mime_type = Column(String(100), nullable=False)  # image/jpeg, video/mp4, etc.
    file_path = Column(String(500), nullable=False)  # Path to file (local or S3)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    
    # Dimensions
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)  # For videos (in seconds)
    
    # Processing
    thumbnail_path = Column(String(500), nullable=True)  # Thumbnail for videos
    processed = Column(Boolean, default=False)  # For async processing
    
    # Metadata
    alt_text = Column(Text, nullable=True)  # Accessibility
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    post = relationship("Post", back_populates="media")
    
    def __repr__(self):
        return f"<Media {self.id} - {self.media_type}>"

