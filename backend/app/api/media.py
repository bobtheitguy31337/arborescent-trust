"""
Media upload API endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
import os

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.post import Media
from app.services.media_service import MediaService
from app.schemas.post import MediaAttachment
from app.core.exceptions import not_found_error

router = APIRouter(prefix="/api/media", tags=["media"])


@router.post("/upload", response_model=MediaAttachment, status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a media file (image, video, or GIF).
    
    Returns media ID to be attached to a post.
    """
    media_service = MediaService(db)
    
    media = await media_service.upload_media(
        file=file,
        user_id=current_user.id,
        alt_text=alt_text
    )
    
    return MediaAttachment(
        id=str(media.id),
        media_type=media.media_type,
        mime_type=media.mime_type,
        file_path=media.file_path,
        width=media.width,
        height=media.height,
        duration=media.duration,
        thumbnail_path=media.thumbnail_path,
        alt_text=media.alt_text
    )


@router.get("/{media_id}")
async def get_media(
    media_id: str,
    db: Session = Depends(get_db)
):
    """Get a media file."""
    media = db.query(Media).filter(Media.id == UUID(media_id)).first()
    
    if not media:
        raise not_found_error("Media not found")
    
    if not os.path.exists(media.file_path):
        raise not_found_error("Media file not found on disk")
    
    return FileResponse(
        media.file_path,
        media_type=media.mime_type,
        filename=os.path.basename(media.file_path)
    )


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a media file."""
    media_service = MediaService(db)
    
    media_service.delete_media(
        media_id=UUID(media_id),
        user_id=current_user.id
    )
    
    return None

