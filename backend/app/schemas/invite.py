"""
Invite token schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InviteCreateRequest(BaseModel):
    """Request schema for creating invite tokens."""
    count: int = Field(1, ge=1, le=10, description="Number of tokens to create (1-10)")
    note: Optional[str] = Field(None, max_length=500, description="Optional note about these invites")


class InviteTokenResponse(BaseModel):
    """Response schema for a single invite token."""
    id: str
    token: str
    created_at: datetime
    expires_at: datetime
    is_used: bool
    is_revoked: bool
    note: Optional[str]
    invite_url: str
    
    class Config:
        from_attributes = True


class InviteCreateResponse(BaseModel):
    """Response schema for invite creation."""
    tokens: List[InviteTokenResponse]
    remaining_quota: int


class InviteValidateResponse(BaseModel):
    """Response schema for invite validation (public endpoint)."""
    valid: bool
    reason: Optional[str] = None
    created_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class InviteListResponse(BaseModel):
    """Response schema for listing user's created invites."""
    tokens: List[InviteTokenResponse]
    total: int
    used_count: int
    available_count: int


class InviteRevokeRequest(BaseModel):
    """Request schema for revoking an invite token."""
    reason: Optional[str] = Field(None, max_length=500)


class InviteRevokeResponse(BaseModel):
    """Response schema for invite revocation."""
    success: bool
    message: str
    credited_back: bool

