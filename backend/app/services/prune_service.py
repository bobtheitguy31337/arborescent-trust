"""
Prune service - handles branch pruning operations (soft delete).
"""

from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.models.prune_operation import PruneOperation
from app.models.audit_log import InviteAuditLog
from app.services.tree_service import TreeService
from app.core.exceptions import not_found_error, bad_request_error


class PruneService:
    """Service for pruning branches from the invite tree."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tree_service = TreeService(db)
    
    def get_affected_users(self, root_user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all users that would be affected by pruning.
        
        Args:
            root_user_id: UUID of root user to prune
            
        Returns:
            List of dicts with user information
        """
        descendants = self.tree_service.get_descendants(root_user_id)
        
        if not descendants:
            raise not_found_error("User not found")
        
        affected = []
        for desc in descendants:
            user = self.db.query(User).filter(User.id == desc["id"]).first()
            if user:
                # Get descendant count for this user
                user_descendants = self.tree_service.get_descendants(user.id)
                
                affected.append({
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "status": user.status,
                    "created_at": user.created_at.isoformat(),
                    "depth": desc["depth"],
                    "descendants_count": len(user_descendants) - 1  # Exclude self
                })
        
        return affected
    
    def execute_prune(
        self,
        root_user_id: UUID,
        reason: str,
        executed_by_user_id: UUID,
        ip_address: str = None,
        user_agent: str = None
    ) -> PruneOperation:
        """
        Execute a prune operation (soft delete entire branch).
        
        Args:
            root_user_id: UUID of root user to prune
            reason: Reason for pruning
            executed_by_user_id: UUID of admin executing the prune
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            PruneOperation object
            
        Raises:
            HTTPException: If validation fails
        """
        # Get all affected users
        affected_users = self.get_affected_users(root_user_id)
        
        if not affected_users:
            raise bad_request_error("No users found to prune")
        
        # Verify root user exists and isn't a core member
        root_user = self.db.query(User).filter(User.id == root_user_id).first()
        if not root_user:
            raise not_found_error("Root user not found")
        
        if root_user.is_core_member:
            raise bad_request_error("Cannot prune a core member")
        
        if root_user.is_deleted:
            raise bad_request_error("User is already deleted")
        
        # Create prune operation record
        prune_op = PruneOperation(
            root_user_id=root_user_id,
            affected_user_count=len(affected_users),
            reason=reason,
            executed_by_user_id=executed_by_user_id,
            status="pending",
            affected_users=affected_users
        )
        
        self.db.add(prune_op)
        self.db.flush()  # Get prune_op.id
        
        # Soft delete all affected users
        now = datetime.utcnow()
        for affected in affected_users:
            user = self.db.query(User).filter(User.id == affected["id"]).first()
            if user and not user.is_deleted:
                user.deleted_at = now
                user.deleted_reason = f"Pruned: {reason}"
                user.status = "banned"
                
                # Log to audit
                audit_entry = InviteAuditLog(
                    event_type="user_pruned",
                    actor_user_id=executed_by_user_id,
                    target_user_id=user.id,
                    event_data={
                        "prune_operation_id": str(prune_op.id),
                        "reason": reason,
                        "depth": affected["depth"]
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                self.db.add(audit_entry)
        
        # Mark operation as completed
        prune_op.status = "completed"
        prune_op.executed_at = now
        
        self.db.commit()
        self.db.refresh(prune_op)
        
        return prune_op
    
    def get_prune_operations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[PruneOperation]:
        """
        Get prune operation history.
        
        Args:
            limit: Maximum number of operations to return
            offset: Number of operations to skip
            
        Returns:
            List of PruneOperation objects
        """
        return self.db.query(PruneOperation).order_by(
            PruneOperation.created_at.desc()
        ).offset(offset).limit(limit).all()
    
    def get_prune_operation(self, operation_id: UUID) -> PruneOperation:
        """
        Get a specific prune operation.
        
        Args:
            operation_id: UUID of operation
            
        Returns:
            PruneOperation object
            
        Raises:
            HTTPException: If operation not found
        """
        operation = self.db.query(PruneOperation).filter(
            PruneOperation.id == operation_id
        ).first()
        
        if not operation:
            raise not_found_error("Prune operation not found")
        
        return operation
    
    def rollback_prune(
        self,
        operation_id: UUID,
        executed_by_user_id: UUID
    ) -> PruneOperation:
        """
        Rollback a prune operation (restore deleted users).
        
        Args:
            operation_id: UUID of operation to rollback
            executed_by_user_id: UUID of admin executing rollback
            
        Returns:
            Updated PruneOperation object
        """
        operation = self.get_prune_operation(operation_id)
        
        if operation.status != "completed":
            raise bad_request_error("Can only rollback completed operations")
        
        # Restore all affected users
        for affected in operation.affected_users:
            user = self.db.query(User).filter(User.id == affected["id"]).first()
            if user and user.is_deleted:
                user.deleted_at = None
                user.deleted_reason = None
                user.status = "active"  # Or restore original status
                
                # Log rollback
                audit_entry = InviteAuditLog(
                    event_type="prune_rolled_back",
                    actor_user_id=executed_by_user_id,
                    target_user_id=user.id,
                    event_data={
                        "prune_operation_id": str(operation_id),
                        "original_reason": operation.reason
                    }
                )
                self.db.add(audit_entry)
        
        operation.status = "rolled_back"
        
        self.db.commit()
        self.db.refresh(operation)
        
        return operation

