"""
Social API endpoints for follows, likes, and notifications.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.social_service import SocialService
from app.schemas.social import (
    FollowRequest,
    FollowResponse,
    UserProfile,
    UserListItem,
    UserListResponse,
    NotificationResponse,
    NotificationListResponse
)

router = APIRouter(prefix="/api/social", tags=["social"])


@router.post("/follow", response_model=FollowResponse, status_code=201)
async def follow_user(
    data: FollowRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a user."""
    social_service = SocialService(db)
    
    follow = social_service.follow_user(
        follower_id=current_user.id,
        following_id=UUID(data.user_id)
    )
    
    return FollowResponse(
        id=str(follow.id),
        follower_id=str(follow.follower_id),
        following_id=str(follow.following_id),
        created_at=follow.created_at
    )


@router.delete("/follow/{user_id}", status_code=204)
async def unfollow_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a user."""
    social_service = SocialService(db)
    
    social_service.unfollow_user(
        follower_id=current_user.id,
        following_id=UUID(user_id)
    )
    
    return None


@router.get("/users/{user_id}/followers", response_model=UserListResponse)
async def get_followers(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get users following a user."""
    social_service = SocialService(db)
    
    result = social_service.get_followers(
        user_id=UUID(user_id),
        page=page,
        page_size=page_size,
        viewer_id=current_user.id
    )
    
    users = [
        UserListItem(
            id=str(item["user"].id),
            username=item["user"].username,
            display_name=item["user"].display_name,
            bio=item["user"].bio,
            avatar_url=item["user"].avatar_url,
            follower_count=item["user"].follower_count,
            is_following=item["is_following"]
        )
        for item in result["users"]
    ]
    
    return UserListResponse(
        users=users,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.get("/users/{user_id}/following", response_model=UserListResponse)
async def get_following(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get users a user is following."""
    social_service = SocialService(db)
    
    result = social_service.get_following(
        user_id=UUID(user_id),
        page=page,
        page_size=page_size,
        viewer_id=current_user.id
    )
    
    users = [
        UserListItem(
            id=str(item["user"].id),
            username=item["user"].username,
            display_name=item["user"].display_name,
            bio=item["user"].bio,
            avatar_url=item["user"].avatar_url,
            follower_count=item["user"].follower_count,
            is_following=item["is_following"]
        )
        for item in result["users"]
    ]
    
    return UserListResponse(
        users=users,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.post("/posts/{post_id}/like", status_code=201)
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Like a post."""
    social_service = SocialService(db)
    
    social_service.like_post(
        user_id=current_user.id,
        post_id=UUID(post_id)
    )
    
    return {"success": True}


@router.delete("/posts/{post_id}/like", status_code=204)
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlike a post."""
    social_service = SocialService(db)
    
    social_service.unlike_post(
        user_id=current_user.id,
        post_id=UUID(post_id)
    )
    
    return None


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for current user."""
    social_service = SocialService(db)
    
    result = social_service.get_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only
    )
    
    notifications = [
        NotificationResponse(
            id=str(n.id),
            user_id=str(n.user_id),
            actor_id=str(n.actor_id) if n.actor_id else None,
            notification_type=n.notification_type.value,
            post_id=str(n.post_id) if n.post_id else None,
            message=n.message,
            extra_data=n.extra_data,
            read=n.read,
            read_at=n.read_at,
            created_at=n.created_at,
            actor=UserListItem(
                id=str(n.actor.id),
                username=n.actor.username,
                display_name=n.actor.display_name,
                bio=n.actor.bio,
                avatar_url=n.actor.avatar_url,
                follower_count=n.actor.follower_count,
                is_following=False
            ) if n.actor else None
        )
        for n in result["notifications"]
    ]
    
    return NotificationListResponse(
        notifications=notifications,
        total=result["total"],
        unread_count=result["unread_count"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    social_service = SocialService(db)
    
    social_service.mark_notification_read(
        notification_id=UUID(notification_id),
        user_id=current_user.id
    )
    
    return None


@router.post("/notifications/read-all", status_code=200)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    social_service = SocialService(db)
    
    count = social_service.mark_all_notifications_read(user_id=current_user.id)
    
    return {"count": count}

