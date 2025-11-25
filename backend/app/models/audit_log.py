"""
Audit Log model - Immutable event log for forensic analysis.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.sql import func

from app.database import Base


class InviteAuditLog(Base):
    """
    Immutable audit log for all invite tree events.
    
    Event Types:
    - token_created: New invite token generated
    - token_used: Token redeemed for registration
    - token_expired: Token expired unused
    - token_revoked: Token manually revoked
    - user_pruned: User removed via prune operation
    - quota_adjusted: User invite quota modified
    - user_flagged: User flagged for review
    - user_status_changed: User status modified
    """
    
    __tablename__ = "invite_audit_log"
    
    # Primary key (auto-incrementing for chronological ordering)
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Event classification
    event_type = Column(String(50), nullable=False, index=True)
    
    # Actors
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    target_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    invite_token_id = Column(UUID(as_uuid=True), ForeignKey("invite_tokens.id"), nullable=True)
    
    # Event data (flexible JSONB for different event types)
    event_data = Column(JSONB, nullable=False, default=dict)
    
    # Timestamp (immutable)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Forensic context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<InviteAuditLog(id={self.id}, event_type='{self.event_type}', created_at={self.created_at})>"

