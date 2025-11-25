"""
Media upload and processing service.
"""

from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Optional, Tuple
from uuid import UUID, uuid4
import os
import shutil
from pathlib import Path
from PIL import Image
import mimetypes

from app.models.post import Media
from app.core.exceptions import validation_error
from app.config import settings


class MediaService:
    """Service for media uploads."""
    
    # Allowed file types
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
    ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES
    
    # Size limits (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    
    def __init__(self, db: Session):
        self.db = db
        # Media directory (configurable via env)
        self.media_dir = Path(getattr(settings, "MEDIA_DIR", "/app/media"))
        self.media_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file
        
        Returns:
            Tuple of (media_type, mime_type)
        
        Raises:
            ValidationError if invalid
        """
        # Check mime type
        mime_type = file.content_type
        if not mime_type or mime_type not in self.ALLOWED_TYPES:
            raise validation_error(f"Unsupported file type: {mime_type}")
        
        # Determine media type
        if mime_type in self.ALLOWED_IMAGE_TYPES:
            media_type = "gif" if mime_type == "image/gif" else "image"
        elif mime_type in self.ALLOWED_VIDEO_TYPES:
            media_type = "video"
        else:
            raise validation_error("Invalid media type")
        
        return media_type, mime_type
    
    async def upload_media(
        self,
        file: UploadFile,
        user_id: UUID,
        alt_text: Optional[str] = None
    ) -> Media:
        """
        Upload and process media file.
        
        Args:
            file: Uploaded file
            user_id: ID of user uploading
            alt_text: Optional alt text for accessibility
        
        Returns:
            Created Media object
        """
        # Validate file
        media_type, mime_type = self.validate_file(file)
        
        # Generate unique filename
        file_id = uuid4()
        extension = mimetypes.guess_extension(mime_type) or ".bin"
        filename = f"{user_id}_{file_id}{extension}"
        file_path = self.media_dir / filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            
            # Check size
            file_size = len(content)
            max_size = self.MAX_VIDEO_SIZE if media_type == "video" else self.MAX_IMAGE_SIZE
            
            if file_size > max_size:
                raise validation_error(f"File too large. Max size: {max_size / 1024 / 1024}MB")
            
            buffer.write(content)
        
        # Process media to get dimensions
        width, height, duration = None, None, None
        thumbnail_path = None
        
        if media_type in ["image", "gif"]:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception as e:
                print(f"Error processing image: {e}")
        
        # Create Media record
        media = Media(
            id=file_id,
            post_id=None,  # Will be set when attached to post
            media_type=media_type,
            mime_type=mime_type,
            file_path=str(file_path),
            file_size=file_size,
            width=width,
            height=height,
            duration=duration,
            thumbnail_path=thumbnail_path,
            alt_text=alt_text,
            processed=True
        )
        
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def delete_media(self, media_id: UUID, user_id: UUID) -> None:
        """
        Delete a media file.
        
        Args:
            media_id: ID of media
            user_id: ID of user (for ownership check)
        """
        media = self.db.query(Media).filter(Media.id == media_id).first()
        
        if not media:
            raise validation_error("Media not found")
        
        # Delete physical file
        if os.path.exists(media.file_path):
            try:
                os.remove(media.file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
        
        # Delete thumbnail if exists
        if media.thumbnail_path and os.path.exists(media.thumbnail_path):
            try:
                os.remove(media.thumbnail_path)
            except Exception as e:
                print(f"Error deleting thumbnail: {e}")
        
        # Delete database record
        self.db.delete(media)
        self.db.commit()

