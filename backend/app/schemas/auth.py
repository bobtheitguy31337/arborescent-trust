"""
Authentication schemas for API requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional


class RegisterRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8)
    invite_token: str = Field(..., min_length=10)
    fingerprint: Optional[str] = None
    
    @validator("username")
    def username_alphanumeric(cls, v):
        """Ensure username contains only valid characters."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (with _ or - allowed)")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Response schema for authentication (login/register)."""
    user_id: str
    username: str
    email: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str


class RefreshResponse(BaseModel):
    """Response schema for token refresh."""
    access_token: str
    token_type: str = "bearer"


class UserMeResponse(BaseModel):
    """Response schema for /auth/me endpoint."""
    id: str
    username: str
    email: str
    role: str
    is_core_member: bool
    invite_quota: int
    invites_used: int
    invites_available: int
    status: str
    created_at: str
    
    class Config:
        from_attributes = True

