"""
Social service for follow system and interactions.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.user import User
from app.models.follow import Follow
from app.models.like import Like
from app.models.post import Post
from app.models.notification import Notification, NotificationType
from app.core.exceptions import not_found_error, validation_error


class SocialService:
    """Service for social interactions."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def follow_user(self, follower_id: UUID, following_id: UUID) -> Follow:
        """
        Follow a user.
        
        Args:
            follower_id: ID of user doing the following
            following_id: ID of user being followed
        
        Returns:
            Created follow relationship
        """
        # Can't follow yourself
        if follower_id == following_id:
            raise validation_error("Cannot follow yourself")
        
        # Check both users exist
        follower = self.db.query(User).filter(User.id == follower_id).first()
        following = self.db.query(User).filter(User.id == following_id).first()
        
        if not follower or not following:
            raise not_found_error("User not found")
        
        # Check if already following
        existing = self.db.query(Follow).filter(
            and_(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        ).first()
        
        if existing:
            raise validation_error("Already following this user")
        
        # Create follow relationship
        follow = Follow(
            follower_id=follower_id,
            following_id=following_id
        )
        
        self.db.add(follow)
        
        # Update counters
        follower.following_count += 1
        following.follower_count += 1
        
        # Create notification
        notification = Notification(
            user_id=following_id,
            actor_id=follower_id,
            notification_type=NotificationType.FOLLOW,
            message=f"{follower.username} started following you"
        )
        self.db.add(notification)
        
        self.db.commit()
        self.db.refresh(follow)
        
        return follow
    
    def unfollow_user(self, follower_id: UUID, following_id: UUID) -> None:
        """
        Unfollow a user.
        
        Args:
            follower_id: ID of user doing the unfollowing
            following_id: ID of user being unfollowed
        """
        follow = self.db.query(Follow).filter(
            and_(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id
            )
        ).first()
        
        if not follow:
            raise not_found_error("Follow relationship not found")
        
        # Update counters
        follower = self.db.query(User).filter(User.id == follower_id).first()
        following = self.db.query(User).filter(User.id == following_id).first()
        
        if follower and follower.following_count > 0:
            follower.following_count -= 1
        if following and following.follower_count > 0:
            following.follower_count -= 1
        
        self.db.delete(follow)
        self.db.commit()
    
    def get_followers(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        viewer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get users following this user.
        
        Args:
            user_id: ID of user
            page: Page number
            page_size: Items per page
            viewer_id: Optional ID of viewing user (to check if they follow each follower)
        
        Returns:
            Dict with users and pagination info
        """
        query = self.db.query(User).join(
            Follow, Follow.follower_id == User.id
        ).filter(Follow.following_id == user_id)
        
        total = query.count()
        users = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Enrich with follow status if viewer provided
        enriched_users = []
        for user in users:
            is_following = False
            if viewer_id:
                is_following = self.db.query(Follow).filter(
                    and_(
                        Follow.follower_id == viewer_id,
                        Follow.following_id == user.id
                    )
                ).first() is not None
            
            enriched_users.append({
                "user": user,
                "is_following": is_following
            })
        
        return {
            "users": enriched_users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    def get_following(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        viewer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get users this user is following.
        
        Args:
            user_id: ID of user
            page: Page number
            page_size: Items per page
            viewer_id: Optional ID of viewing user
        
        Returns:
            Dict with users and pagination info
        """
        query = self.db.query(User).join(
            Follow, Follow.following_id == User.id
        ).filter(Follow.follower_id == user_id)
        
        total = query.count()
        users = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Enrich with follow status
        enriched_users = []
        for user in users:
            is_following = False
            if viewer_id:
                is_following = self.db.query(Follow).filter(
                    and_(
                        Follow.follower_id == viewer_id,
                        Follow.following_id == user.id
                    )
                ).first() is not None
            
            enriched_users.append({
                "user": user,
                "is_following": is_following
            })
        
        return {
            "users": enriched_users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    def like_post(self, user_id: UUID, post_id: UUID) -> Like:
        """
        Like a post.
        
        Args:
            user_id: ID of user liking
            post_id: ID of post to like
        
        Returns:
            Created like
        """
        # Check post exists
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise not_found_error("Post not found")
        
        # Check if already liked
        existing = self.db.query(Like).filter(
            and_(Like.user_id == user_id, Like.post_id == post_id)
        ).first()
        
        if existing:
            raise validation_error("Already liked this post")
        
        # Create like
        like = Like(user_id=user_id, post_id=post_id)
        self.db.add(like)
        
        # Update post like count
        post.like_count += 1
        
        # Create notification (if not own post)
        if post.user_id != user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            notification = Notification(
                user_id=post.user_id,
                actor_id=user_id,
                post_id=post_id,
                notification_type=NotificationType.LIKE,
                message=f"{user.username} liked your post"
            )
            self.db.add(notification)
        
        self.db.commit()
        self.db.refresh(like)
        
        return like
    
    def unlike_post(self, user_id: UUID, post_id: UUID) -> None:
        """
        Unlike a post.
        
        Args:
            user_id: ID of user unliking
            post_id: ID of post to unlike
        """
        like = self.db.query(Like).filter(
            and_(Like.user_id == user_id, Like.post_id == post_id)
        ).first()
        
        if not like:
            raise not_found_error("Like not found")
        
        # Update post like count
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if post and post.like_count > 0:
            post.like_count -= 1
        
        self.db.delete(like)
        self.db.commit()
    
    def get_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of user
            page: Page number
            page_size: Items per page
            unread_only: Only return unread notifications
        
        Returns:
            Dict with notifications and pagination info
        """
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id
        )
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        query = query.order_by(desc(Notification.created_at))
        
        total = query.count()
        unread_count = self.db.query(Notification).filter(
            and_(Notification.user_id == user_id, Notification.read == False)
        ).count()
        
        notifications = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "notifications": notifications,
            "total": total,
            "unread_count": unread_count,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    def mark_notification_read(self, notification_id: UUID, user_id: UUID) -> None:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of notification
            user_id: ID of user (for ownership check)
        """
        notification = self.db.query(Notification).filter(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        ).first()
        
        if not notification:
            raise not_found_error("Notification not found")
        
        notification.read = True
        notification.read_at = datetime.utcnow()
        
        self.db.commit()
    
    def mark_all_notifications_read(self, user_id: UUID) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: ID of user
        
        Returns:
            Number of notifications marked as read
        """
        count = self.db.query(Notification).filter(
            and_(
                Notification.user_id == user_id,
                Notification.read == False
            )
        ).update({
            "read": True,
            "read_at": datetime.utcnow()
        })
        
        self.db.commit()
        
        return count

