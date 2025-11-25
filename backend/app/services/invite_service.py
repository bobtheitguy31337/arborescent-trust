"""
Invite service - handles invite token generation, validation, and management.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.user import User
from app.models.invite_token import InviteToken
from app.models.audit_log import InviteAuditLog
from app.core.security import generate_secure_token
from app.core.exceptions import InsufficientQuotaException, bad_request_error, not_found_error
from app.config import settings


class InviteService:
    """Service for invite token operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tokens(
        self,
        user: User,
        count: int = 1,
        note: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> List[InviteToken]:
        """
        Create invite tokens for a user.
        
        Args:
            user: User creating the tokens
            count: Number of tokens to create
            note: Optional note about the tokens
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            List of created InviteToken objects
            
        Raises:
            InsufficientQuotaException: If user doesn't have enough quota
        """
        # Check quota
        available = user.invites_available
        if available < count:
            raise InsufficientQuotaException(
                f"Insufficient invite quota. Available: {available}, Requested: {count}"
            )
        
        # Generate tokens
        tokens = []
        expires_at = datetime.utcnow() + timedelta(hours=settings.INVITE_TOKEN_EXPIRY_HOURS)
        
        for _ in range(count):
            token = InviteToken(
                token=generate_secure_token(),
                created_by_user_id=user.id,
                expires_at=expires_at,
                note=note
            )
            self.db.add(token)
            tokens.append(token)
        
        # Update user's invite usage
        user.invites_used += count
        
        # Flush to get token IDs
        self.db.flush()
        
        # Log to audit
        for token in tokens:
            audit_entry = InviteAuditLog(
                event_type="token_created",
                actor_user_id=user.id,
                target_user_id=user.id,
                invite_token_id=token.id,
                event_data={
                    "token": token.token[:8] + "...",
                    "expires_at": expires_at.isoformat(),
                    "note": note
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(audit_entry)
        
        self.db.commit()
        
        for token in tokens:
            self.db.refresh(token)
        
        return tokens
    
    def validate_token(self, token_str: str) -> Optional[InviteToken]:
        """
        Validate an invite token (public endpoint).
        
        Args:
            token_str: Token string to validate
            
        Returns:
            InviteToken if valid, None otherwise
        """
        token = self.db.query(InviteToken).filter(
            InviteToken.token == token_str
        ).first()
        
        if not token:
            return None
        
        if not token.is_valid:
            return None
        
        return token
    
    def get_user_tokens(self, user_id: UUID) -> List[InviteToken]:
        """
        Get all tokens created by a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            List of InviteToken objects
        """
        return self.db.query(InviteToken).filter(
            InviteToken.created_by_user_id == user_id
        ).order_by(InviteToken.created_at.desc()).all()
    
    def revoke_token(
        self,
        token_id: UUID,
        user: User,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> InviteToken:
        """
        Revoke an invite token.
        
        Args:
            token_id: Token UUID to revoke
            user: User performing the revocation
            reason: Optional reason for revocation
            ip_address: IP address of request
            user_agent: User agent string
            
        Returns:
            Revoked InviteToken
            
        Raises:
            HTTPException: If token not found or user not authorized
        """
        token = self.db.query(InviteToken).filter(
            InviteToken.id == token_id
        ).first()
        
        if not token:
            raise not_found_error("Invite token not found")
        
        # Check authorization (must be creator or admin)
        if token.created_by_user_id != user.id and not user.is_admin:
            raise bad_request_error("Not authorized to revoke this token")
        
        if token.is_used:
            raise bad_request_error("Cannot revoke a token that has already been used")
        
        if token.is_revoked:
            raise bad_request_error("Token is already revoked")
        
        # Revoke token
        token.is_revoked = True
        token.revoked_at = datetime.utcnow()
        token.revoked_by_user_id = user.id
        token.revoked_reason = reason
        
        # Credit back to creator if not expired
        credited_back = False
        if not token.is_expired:
            creator = self.db.query(User).filter(User.id == token.created_by_user_id).first()
            if creator:
                creator.invites_used -= 1
                credited_back = True
        
        # Log to audit
        audit_entry = InviteAuditLog(
            event_type="token_revoked",
            actor_user_id=user.id,
            target_user_id=token.created_by_user_id,
            invite_token_id=token.id,
            event_data={
                "token": token.token[:8] + "...",
                "reason": reason,
                "credited_back": credited_back
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(audit_entry)
        
        self.db.commit()
        self.db.refresh(token)
        
        return token
    
    def expire_unused_tokens(self) -> int:
        """
        Background task: Expire unused tokens and credit back to creators.
        
        Returns:
            Number of tokens expired
        """
        now = datetime.utcnow()
        
        # Find expired tokens that aren't marked as expired yet
        expired_tokens = self.db.query(InviteToken).filter(
            InviteToken.expires_at < now,
            InviteToken.is_used == False,
            InviteToken.is_revoked == False
        ).all()
        
        for token in expired_tokens:
            # Mark as revoked (expired)
            token.is_revoked = True
            token.revoked_reason = "Auto-expired"
            token.revoked_at = now
            
            # Credit back to creator
            creator = self.db.query(User).filter(User.id == token.created_by_user_id).first()
            if creator:
                creator.invites_used -= 1
            
            # Log to audit
            audit_entry = InviteAuditLog(
                event_type="token_expired",
                actor_user_id=None,
                target_user_id=token.created_by_user_id,
                invite_token_id=token.id,
                event_data={
                    "token": token.token[:8] + "...",
                    "expired_at": now.isoformat()
                }
            )
            self.db.add(audit_entry)
        
        self.db.commit()
        
        return len(expired_tokens)

