"""
Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    RefreshRequest,
    RefreshResponse,
    UserMeResponse
)
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: RegisterRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user with an invite token.
    
    - **email**: Valid email address
    - **username**: Alphanumeric username (3-50 chars)
    - **password**: Password (min 8 chars)
    - **invite_token**: Valid invite token from existing user
    - **fingerprint**: Optional device fingerprint
    
    Returns access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    # Capture forensic data
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    # Register user
    user = auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
        invite_token_str=request.invite_token,
        registration_ip=client_ip,
        registration_user_agent=user_agent,
        registration_fingerprint=request.fingerprint
    )
    
    # Generate tokens
    from app.core.security import create_access_token, create_refresh_token
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return AuthResponse(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access and refresh tokens.
    """
    auth_service = AuthService(db)
    
    user, access_token, refresh_token = auth_service.login(
        email=request.email,
        password=request.password
    )
    
    return AuthResponse(
        user_id=str(user.id),
        username=user.username,
        email=user.email,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Returns new access token.
    """
    auth_service = AuthService(db)
    
    new_access_token = auth_service.refresh_access_token(request.refresh_token)
    
    return RefreshResponse(access_token=new_access_token)


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Requires valid access token.
    """
    return UserMeResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_core_member=current_user.is_core_member,
        invite_quota=current_user.invite_quota,
        invites_used=current_user.invites_used,
        invites_available=current_user.invites_available,
        status=current_user.status,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user.
    
    Note: Client should discard tokens. Token blacklisting can be added with Redis.
    """
    return {"message": "Successfully logged out"}

