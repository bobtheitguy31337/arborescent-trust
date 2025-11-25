"""
Post schemas for API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class MediaAttachment(BaseModel):
    """Media attachment in a post."""
    id: str
    media_type: str  # image, video, gif
    mime_type: str
    file_path: str
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    thumbnail_path: Optional[str] = None
    alt_text: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserBasic(BaseModel):
    """Basic user info for post display."""
    id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    """Request to create a new post."""
    content: str = Field(..., min_length=1, max_length=280)
    visibility: str = Field(default="public", pattern="^(public|followers|mentioned)$")
    reply_to_id: Optional[str] = None
    media_ids: Optional[List[str]] = Field(default=None, max_items=4)  # Max 4 media attachments
    
    @validator("content")
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Post content cannot be empty")
        return v


class PostResponse(BaseModel):
    """Post response."""
    id: str
    user_id: str
    content: str
    visibility: str
    
    # Reply info
    is_reply: bool
    reply_to_id: Optional[str] = None
    reply_to_user_id: Optional[str] = None
    
    # Repost info
    is_repost: bool
    repost_of_id: Optional[str] = None
    repost_of: Optional["PostResponse"] = None  # Nested post for reposts
    
    # Engagement
    like_count: int
    repost_count: int
    reply_count: int
    view_count: int
    
    # User interaction state (for current user)
    is_liked: Optional[bool] = False
    is_reposted: Optional[bool] = False
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Related data
    author: UserBasic
    media: List[MediaAttachment] = []
    
    class Config:
        from_attributes = True


# Enable forward reference
PostResponse.model_rebuild()


class FeedResponse(BaseModel):
    """Feed response with pagination."""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class RepostRequest(BaseModel):
    """Request to repost."""
    post_id: str
    comment: Optional[str] = Field(None, max_length=280)  # Optional comment on repost


class PostStatsResponse(BaseModel):
    """Post statistics."""
    total_posts: int
    total_likes: int
    total_reposts: int
    posts_today: int
    posts_this_week: int

