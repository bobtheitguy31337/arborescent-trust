"""
Social schemas for follow system and interactions.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FollowRequest(BaseModel):
    """Request to follow a user."""
    user_id: str


class FollowResponse(BaseModel):
    """Follow relationship response."""
    id: str
    follower_id: str
    following_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Full user profile for social display."""
    id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    
    # Counts
    follower_count: int
    following_count: int
    post_count: int
    
    # Trust system
    status: str
    is_core_member: bool
    
    # Current user's relationship
    is_following: Optional[bool] = False
    is_followed_by: Optional[bool] = False
    
    # Timestamps
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """User item in a list (followers/following)."""
    id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: int
    is_following: Optional[bool] = False
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list."""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationResponse(BaseModel):
    """Notification response."""
    id: str
    user_id: str
    actor_id: Optional[str] = None
    notification_type: str
    post_id: Optional[str] = None
    message: Optional[str] = None
    extra_data: Optional[dict] = None
    read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    
    # Related data
    actor: Optional[UserListItem] = None
    
    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notification list."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    has_more: bool

