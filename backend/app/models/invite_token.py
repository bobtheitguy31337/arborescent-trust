"""
Invite Token model - Represents a single-use invite code.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.database import Base


class InviteToken(Base):
    """
    Invite token for user registration.
    
    Each token is:
    - Single-use only
    - Time-limited (24h default)
    - Cryptographically secure
    - Traceable back to creator
    """
    
    __tablename__ = "invite_tokens"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # The actual token string (64 chars, cryptographically secure)
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Ownership
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Usage
    used_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    is_used = Column(Boolean, default=False, index=True)
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Revocation
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    revoked_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Forensic metadata
    used_ip = Column(INET, nullable=True)
    used_user_agent = Column(Text, nullable=True)
    
    # Optional note from creator
    note = Column(Text, nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_tokens")
    used_by_user = relationship("User", foreign_keys=[used_by_user_id], back_populates="used_token")
    
    def __repr__(self):
        return f"<InviteToken(id={self.id}, token={self.token[:8]}..., is_used={self.is_used})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if token is valid for use."""
        now = datetime.utcnow()
        return (
            not self.is_used
            and not self.is_revoked
            and self.expires_at > now
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return datetime.utcnow() > self.expires_at

