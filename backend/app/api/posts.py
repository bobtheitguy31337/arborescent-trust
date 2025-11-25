"""
Posts API endpoints.
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.post import Post, Media
from app.services.post_service import PostService
from app.schemas.post import (
    PostCreate,
    PostResponse,
    FeedResponse,
    RepostRequest,
    PostStatsResponse,
    MediaAttachment,
    UserBasic
)
from app.core.exceptions import validation_error

router = APIRouter(prefix="/api/posts", tags=["posts"])


def enrich_post_response(post_data: dict, db: Session) -> PostResponse:
    """Helper to convert post data to response schema."""
    post = post_data["post"]
    
    # Load author
    author = UserBasic(
        id=str(post.user_id),
        username=post.author.username,
        display_name=post.author.display_name,
        avatar_url=post.author.avatar_url
    )
    
    # Load media
    media_list = [
        MediaAttachment(
            id=str(m.id),
            media_type=m.media_type,
            mime_type=m.mime_type,
            file_path=m.file_path,
            width=m.width,
            height=m.height,
            duration=m.duration,
            thumbnail_path=m.thumbnail_path,
            alt_text=m.alt_text
        )
        for m in post.media
    ]
    
    # Load reposted post if applicable
    repost_of = None
    if post.is_repost and post.repost_of_id:
        original = db.query(Post).filter(Post.id == post.repost_of_id).first()
        if original:
            repost_of = PostResponse(
                id=str(original.id),
                user_id=str(original.user_id),
                content=original.content,
                visibility=original.visibility,
                is_reply=original.is_reply,
                reply_to_id=str(original.reply_to_id) if original.reply_to_id else None,
                reply_to_user_id=str(original.reply_to_user_id) if original.reply_to_user_id else None,
                is_repost=False,
                repost_of_id=None,
                like_count=original.like_count,
                repost_count=original.repost_count,
                reply_count=original.reply_count,
                view_count=original.view_count,
                created_at=original.created_at,
                updated_at=original.updated_at,
                author=UserBasic(
                    id=str(original.author.id),
                    username=original.author.username,
                    display_name=original.author.display_name,
                    avatar_url=original.author.avatar_url
                ),
                media=[]
            )
    
    return PostResponse(
        id=str(post.id),
        user_id=str(post.user_id),
        content=post.content,
        visibility=post.visibility,
        is_reply=post.is_reply,
        reply_to_id=str(post.reply_to_id) if post.reply_to_id else None,
        reply_to_user_id=str(post.reply_to_user_id) if post.reply_to_user_id else None,
        is_repost=post.is_repost,
        repost_of_id=str(post.repost_of_id) if post.repost_of_id else None,
        repost_of=repost_of,
        like_count=post.like_count,
        repost_count=post.repost_count,
        reply_count=post.reply_count,
        view_count=post.view_count,
        is_liked=post_data.get("is_liked", False),
        is_reposted=post_data.get("is_reposted", False),
        created_at=post.created_at,
        updated_at=post.updated_at,
        author=author,
        media=media_list
    )


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new post."""
    post_service = PostService(db)
    
    post = post_service.create_post(
        user_id=current_user.id,
        content=data.content,
        visibility=data.visibility,
        reply_to_id=UUID(data.reply_to_id) if data.reply_to_id else None,
        media_ids=data.media_ids
    )
    
    post_data = {"post": post, "is_liked": False, "is_reposted": False}
    return enrich_post_response(post_data, db)


@router.post("/repost", response_model=PostResponse, status_code=201)
async def create_repost(
    data: RepostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Repost a post."""
    post_service = PostService(db)
    
    repost = post_service.create_repost(
        user_id=current_user.id,
        post_id=UUID(data.post_id),
        comment=data.comment
    )
    
    post_data = {"post": repost, "is_liked": False, "is_reposted": True}
    return enrich_post_response(post_data, db)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized feed for current user."""
    post_service = PostService(db)
    
    result = post_service.get_feed(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    posts = [enrich_post_response(p, db) for p in result["posts"]]
    
    return FeedResponse(
        posts=posts,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single post."""
    post_service = PostService(db)
    
    post_data = post_service.get_post(
        post_id=UUID(post_id),
        viewer_id=current_user.id
    )
    
    if not post_data:
        raise validation_error("Post not found")
    
    return enrich_post_response(post_data, db)


@router.get("/{post_id}/replies", response_model=FeedResponse)
async def get_post_replies(
    post_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get replies to a post."""
    post_service = PostService(db)
    
    result = post_service.get_replies(
        post_id=UUID(post_id),
        page=page,
        page_size=page_size
    )
    
    posts = [enrich_post_response(p, db) for p in result["posts"]]
    
    return FeedResponse(
        posts=posts,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a post."""
    post_service = PostService(db)
    
    post_service.delete_post(
        post_id=UUID(post_id),
        user_id=current_user.id
    )
    
    return None


@router.get("/user/{user_id}", response_model=FeedResponse)
async def get_user_posts(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get posts by a specific user."""
    post_service = PostService(db)
    
    result = post_service.get_user_posts(
        user_id=UUID(user_id),
        page=page,
        page_size=page_size,
        viewer_id=current_user.id
    )
    
    posts = [enrich_post_response(p, db) for p in result["posts"]]
    
    return FeedResponse(
        posts=posts,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        has_more=result["has_more"]
    )

