"""
User model - Core entity in the invite tree system.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class User(Base):
    """
    User model representing a node in the invite tree.
    
    Each user (except core members) must be invited by another user,
    creating a tree structure that enables forensic analysis and surgical pruning.
    """
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User type & role
    is_core_member = Column(Boolean, default=False)
    role = Column(String(20), default="user")  # user, admin, superadmin
    
    # Invite capacity
    invite_quota = Column(Integer, default=0)
    invites_used = Column(Integer, default=0)
    
    # Tree relationship - THE CRITICAL FIELD
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default="active", index=True)  # active, suspended, banned, flagged
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Forensic data (captured at registration)
    registration_ip = Column(INET, nullable=True)
    registration_user_agent = Column(Text, nullable=True)
    registration_fingerprint = Column(String(255), nullable=True)
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    deleted_reason = Column(Text, nullable=True)
    
    # Relationships
    invited_by = relationship("User", remote_side=[id], backref="invited_users")
    created_tokens = relationship("InviteToken", foreign_keys="InviteToken.created_by_user_id", back_populates="creator")
    used_token = relationship("InviteToken", foreign_keys="InviteToken.used_by_user_id", back_populates="used_by_user", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', status='{self.status}')>"
    
    @property
    def invites_available(self) -> int:
        """Calculate remaining invite quota."""
        return max(0, self.invite_quota - self.invites_used)
    
    @property
    def is_deleted(self) -> bool:
        """Check if user is soft-deleted."""
        return self.deleted_at is not None
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in ["admin", "superadmin"]

