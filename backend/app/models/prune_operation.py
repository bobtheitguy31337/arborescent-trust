"""
Prune Operation model - Records branch removal operations.
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.database import Base


class PruneOperation(Base):
    """
    Record of a branch pruning operation.
    
    Stores:
    - Which user was the root of the pruned branch
    - How many users were affected
    - Why the prune was executed
    - Full snapshot of affected users (for potential rollback)
    """
    
    __tablename__ = "prune_operations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Target
    root_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Operation details
    affected_user_count = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    
    # Decision maker
    executed_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="pending")  # pending, completed, rolled_back
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Snapshot of affected users (JSONB array)
    affected_users = Column(JSONB, nullable=False, default=list)
    
    def __repr__(self):
        return f"<PruneOperation(id={self.id}, root_user_id={self.root_user_id}, affected_count={self.affected_user_count}, status='{self.status}')>"

