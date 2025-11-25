"""
Post service for social media functionality.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.models.post import Post, Media
from app.models.user import User
from app.models.follow import Follow
from app.models.like import Like
from app.core.exceptions import not_found_error, forbidden_error, validation_error


class PostService:
    """Service for post-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_post(
        self,
        user_id: UUID,
        content: str,
        visibility: str = "public",
        reply_to_id: Optional[UUID] = None,
        media_ids: Optional[List[str]] = None
    ) -> Post:
        """
        Create a new post.
        
        Args:
            user_id: ID of user creating the post
            content: Post content (max 280 chars)
            visibility: Post visibility (public, followers, mentioned)
            reply_to_id: Optional ID of post being replied to
            media_ids: Optional list of media IDs to attach
        
        Returns:
            Created post
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise not_found_error("User not found")
        
        # If reply, validate parent post exists
        reply_to_user_id = None
        if reply_to_id:
            parent_post = self.db.query(Post).filter(Post.id == reply_to_id).first()
            if not parent_post:
                raise not_found_error("Parent post not found")
            reply_to_user_id = parent_post.user_id
        
        # Create post
        post = Post(
            user_id=user_id,
            content=content,
            visibility=visibility,
            reply_to_id=reply_to_id,
            reply_to_user_id=reply_to_user_id,
            is_reply=reply_to_id is not None
        )
        
        self.db.add(post)
        self.db.flush()  # Get post ID
        
        # Attach media if provided
        if media_ids:
            media_records = self.db.query(Media).filter(Media.id.in_([UUID(mid) for mid in media_ids])).all()
            for media in media_records:
                media.post_id = post.id
        
        # Update parent post reply count
        if reply_to_id:
            self.db.query(Post).filter(Post.id == reply_to_id).update(
                {"reply_count": Post.reply_count + 1}
            )
        
        # Update user post count
        user.post_count += 1
        
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def create_repost(self, user_id: UUID, post_id: UUID, comment: Optional[str] = None) -> Post:
        """
        Create a repost (like retweet).
        
        Args:
            user_id: ID of user reposting
            post_id: ID of post to repost
            comment: Optional comment on the repost
        
        Returns:
            Created repost
        """
        # Validate original post exists
        original_post = self.db.query(Post).filter(Post.id == post_id).first()
        if not original_post:
            raise not_found_error("Post not found")
        
        # Check if already reposted
        existing = self.db.query(Post).filter(
            and_(
                Post.user_id == user_id,
                Post.repost_of_id == post_id,
                Post.deleted_at == None
            )
        ).first()
        
        if existing:
            raise validation_error("Already reposted")
        
        # Create repost
        repost = Post(
            user_id=user_id,
            content=comment or "",
            repost_of_id=post_id,
            is_repost=True,
            visibility=original_post.visibility
        )
        
        self.db.add(repost)
        
        # Update original post repost count
        original_post.repost_count += 1
        
        # Update user post count
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.post_count += 1
        
        self.db.commit()
        self.db.refresh(repost)
        
        return repost
    
    def delete_post(self, post_id: UUID, user_id: UUID) -> None:
        """
        Soft delete a post.
        
        Args:
            post_id: ID of post to delete
            user_id: ID of user requesting deletion
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise not_found_error("Post not found")
        
        # Check ownership
        if str(post.user_id) != str(user_id):
            raise forbidden_error("Can only delete your own posts")
        
        # Soft delete
        post.deleted_at = datetime.utcnow()
        
        # Update user post count
        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.post_count > 0:
            user.post_count -= 1
        
        self.db.commit()
    
    def get_post(self, post_id: UUID, viewer_id: Optional[UUID] = None) -> Optional[Dict[str, Any]]:
        """
        Get a single post with engagement data.
        
        Args:
            post_id: ID of post
            viewer_id: Optional ID of viewing user (to check if liked/reposted)
        
        Returns:
            Post dict with all data or None
        """
        post = self.db.query(Post).filter(
            and_(Post.id == post_id, Post.deleted_at == None)
        ).first()
        
        if not post:
            return None
        
        # Check if viewer has liked/reposted
        is_liked = False
        is_reposted = False
        
        if viewer_id:
            is_liked = self.db.query(Like).filter(
                and_(Like.post_id == post_id, Like.user_id == viewer_id)
            ).first() is not None
            
            is_reposted = self.db.query(Post).filter(
                and_(
                    Post.user_id == viewer_id,
                    Post.repost_of_id == post_id,
                    Post.deleted_at == None
                )
            ).first() is not None
        
        # Increment view count
        post.view_count += 1
        self.db.commit()
        
        return {
            "post": post,
            "is_liked": is_liked,
            "is_reposted": is_reposted
        }
    
    def get_user_posts(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        viewer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get posts by a specific user.
        
        Args:
            user_id: ID of user whose posts to fetch
            page: Page number
            page_size: Items per page
            viewer_id: Optional ID of viewing user
        
        Returns:
            Dict with posts and pagination info
        """
        query = self.db.query(Post).filter(
            and_(
                Post.user_id == user_id,
                Post.deleted_at == None,
                Post.is_repost == False  # Exclude bare reposts, include quoted reposts
            )
        ).order_by(desc(Post.created_at))
        
        total = query.count()
        posts = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Enrich with engagement data
        enriched_posts = []
        for post in posts:
            is_liked = False
            is_reposted = False
            
            if viewer_id:
                is_liked = self.db.query(Like).filter(
                    and_(Like.post_id == post.id, Like.user_id == viewer_id)
                ).first() is not None
                
                is_reposted = self.db.query(Post).filter(
                    and_(
                        Post.user_id == viewer_id,
                        Post.repost_of_id == post.id,
                        Post.deleted_at == None
                    )
                ).first() is not None
            
            enriched_posts.append({
                "post": post,
                "is_liked": is_liked,
                "is_reposted": is_reposted
            })
        
        return {
            "posts": enriched_posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    def get_feed(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Get personalized feed for a user.
        
        Shows posts from:
        - Users they follow
        - Their own posts
        
        Ordered by recency (can be enhanced with algorithm later).
        
        Args:
            user_id: ID of user requesting feed
            page: Page number
            page_size: Items per page
        
        Returns:
            Dict with posts and pagination info
        """
        # Get list of users the current user follows
        following_ids = self.db.query(Follow.following_id).filter(
            Follow.follower_id == user_id
        ).subquery()
        
        # Query posts from followed users and self
        query = self.db.query(Post).filter(
            and_(
                or_(
                    Post.user_id.in_(following_ids),
                    Post.user_id == user_id
                ),
                Post.deleted_at == None,
                Post.visibility.in_(["public", "followers"])
            )
        ).order_by(desc(Post.created_at))
        
        total = query.count()
        posts = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Enrich with engagement data
        enriched_posts = []
        for post in posts:
            is_liked = self.db.query(Like).filter(
                and_(Like.post_id == post.id, Like.user_id == user_id)
            ).first() is not None
            
            is_reposted = self.db.query(Post).filter(
                and_(
                    Post.user_id == user_id,
                    Post.repost_of_id == post.id,
                    Post.deleted_at == None
                )
            ).first() is not None
            
            enriched_posts.append({
                "post": post,
                "is_liked": is_liked,
                "is_reposted": is_reposted
            })
        
        return {
            "posts": enriched_posts,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }
    
    def get_replies(self, post_id: UUID, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Get replies to a post.
        
        Args:
            post_id: ID of parent post
            page: Page number
            page_size: Items per page
        
        Returns:
            Dict with replies and pagination info
        """
        query = self.db.query(Post).filter(
            and_(
                Post.reply_to_id == post_id,
                Post.deleted_at == None
            )
        ).order_by(Post.created_at)
        
        total = query.count()
        replies = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "posts": [{"post": post, "is_liked": False, "is_reposted": False} for post in replies],
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_more": (page * page_size) < total
        }

