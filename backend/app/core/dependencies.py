"""
FastAPI dependency injection functions.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.core.security import verify_token
from app.core.exceptions import unauthorized_error, forbidden_error


# Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    This dependency extracts the JWT token from the Authorization header,
    validates it, and returns the corresponding User object.
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None:
            raise unauthorized_error("Invalid token")
        
        if token_type != "access":
            raise unauthorized_error("Invalid token type")
            
    except JWTError:
        raise unauthorized_error("Invalid token")
    
    # Fetch user from database
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    if user is None:
        raise unauthorized_error("User not found")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are active.
    
    Raises:
        HTTPException: 403 if user is not active
    """
    if current_user.status not in ["active"]:
        raise forbidden_error(f"Account is {current_user.status}")
    
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin role for endpoint access.
    
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if current_user.role not in ["admin", "superadmin"]:
        raise forbidden_error("Admin access required")
    
    return current_user


async def require_superadmin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require superadmin role for endpoint access.
    
    Raises:
        HTTPException: 403 if user is not a superadmin
    """
    if current_user.role != "superadmin":
        raise forbidden_error("Superadmin access required")
    
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None.
    
    Useful for endpoints that have optional authentication.
    """
    if credentials is None:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id:
            user = db.query(User).filter(
                User.id == user_id,
                User.deleted_at == None
            ).first()
            return user
    except JWTError:
        pass
    
    return None

