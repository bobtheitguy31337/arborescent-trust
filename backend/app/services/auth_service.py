"""
Authentication service - handles user registration, login, and token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.invite_token import InviteToken
from app.models.audit_log import InviteAuditLog
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import InvalidInviteTokenException, bad_request_error, unauthorized_error
from app.config import settings


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(
        self,
        email: str,
        username: str,
        password: str,
        invite_token_str: str,
        registration_ip: Optional[str] = None,
        registration_user_agent: Optional[str] = None,
        registration_fingerprint: Optional[str] = None
    ) -> User:
        """
        Register a new user with an invite token.
        
        Args:
            email: User's email address
            username: Unique username
            password: Plain text password (will be hashed)
            invite_token_str: Invite token string
            registration_ip: IP address of registration
            registration_user_agent: User agent string
            registration_fingerprint: Device fingerprint
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If validation fails
        """
        # Check if email already exists
        if self.db.query(User).filter(User.email == email).first():
            raise bad_request_error("Email already registered")
        
        # Check if username already exists
        if self.db.query(User).filter(User.username == username).first():
            raise bad_request_error("Username already taken")
        
        # Validate invite token
        invite_token = self.db.query(InviteToken).filter(
            InviteToken.token == invite_token_str
        ).first()
        
        if not invite_token:
            raise bad_request_error("Invalid invite token")
        
        if not invite_token.is_valid:
            if invite_token.is_used:
                reason = "Invite token has already been used"
            elif invite_token.is_revoked:
                reason = "Invite token has been revoked"
            elif invite_token.is_expired:
                reason = "Invite token has expired"
            else:
                reason = "Invite token is invalid"
            raise bad_request_error(reason)
        
        # Create user
        user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            invited_by_user_id=invite_token.created_by_user_id,
            invite_quota=settings.DEFAULT_INVITE_QUOTA,
            registration_ip=registration_ip,
            registration_user_agent=registration_user_agent,
            registration_fingerprint=registration_fingerprint,
            status="active"
        )
        
        self.db.add(user)
        self.db.flush()  # Get user.id without committing
        
        # Mark token as used
        invite_token.is_used = True
        invite_token.used_by_user_id = user.id
        invite_token.used_at = datetime.utcnow()
        invite_token.used_ip = registration_ip
        invite_token.used_user_agent = registration_user_agent
        
        # Log to audit
        audit_entry = InviteAuditLog(
            event_type="token_used",
            actor_user_id=user.id,
            target_user_id=invite_token.created_by_user_id,
            invite_token_id=invite_token.id,
            event_data={
                "new_user_email": email,
                "new_user_username": username,
                "token": invite_token_str[:8] + "..."
            },
            ip_address=registration_ip,
            user_agent=registration_user_agent
        )
        self.db.add(audit_entry)
        
        # Commit transaction
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(
            User.email == email,
            User.deleted_at == None
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Login user and generate tokens.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            Tuple of (User, access_token, refresh_token)
            
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(email, password)
        
        if not user:
            raise unauthorized_error("Incorrect email or password")
        
        if user.status != "active":
            raise bad_request_error(f"Account is {user.status}")
        
        # Generate tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        
        return user, access_token, refresh_token
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token
            
        Raises:
            HTTPException: If refresh token is invalid
        """
        from jose import jwt, JWTError
        
        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            user_id = payload.get("sub")
            token_type = payload.get("type")
            
            if user_id is None or token_type != "refresh":
                raise unauthorized_error("Invalid refresh token")
            
            # Verify user still exists and is active
            user = self.db.query(User).filter(
                User.id == user_id,
                User.deleted_at == None
            ).first()
            
            if not user or user.status != "active":
                raise unauthorized_error("Invalid refresh token")
            
            # Generate new access token
            new_access_token = create_access_token(user_id)
            
            return new_access_token
            
        except JWTError:
            raise unauthorized_error("Invalid refresh token")

