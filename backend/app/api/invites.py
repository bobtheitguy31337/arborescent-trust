"""
Invite token API endpoints.
"""

from fastapi import APIRouter, Depends, Request, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.invite import (
    InviteCreateRequest,
    InviteCreateResponse,
    InviteValidateResponse,
    InviteListResponse,
    InviteRevokeRequest,
    InviteRevokeResponse,
    InviteTokenResponse
)
from app.services.invite_service import InviteService
from app.core.dependencies import get_current_user
from app.core.exceptions import InsufficientQuotaException, bad_request_error
from app.models.user import User
from app.config import settings


router = APIRouter(prefix="/api/invites", tags=["Invites"])


def build_invite_url(token: str) -> str:
    """Build public invite URL."""
    # In production, this would use your frontend domain
    return f"https://app.example.com/invite/{token}"


@router.post("/create", response_model=InviteCreateResponse, status_code=201)
async def create_invites(
    request: InviteCreateRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new invite tokens.
    
    - **count**: Number of tokens to create (1-10)
    - **note**: Optional note about these invites
    
    Requires sufficient invite quota.
    """
    invite_service = InviteService(db)
    
    # Capture metadata
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    try:
        tokens = invite_service.create_tokens(
            user=current_user,
            count=request.count,
            note=request.note,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except InsufficientQuotaException as e:
        raise bad_request_error(str(e))
    
    # Build response
    token_responses = [
        InviteTokenResponse(
            id=str(token.id),
            token=token.token,
            created_at=token.created_at,
            expires_at=token.expires_at,
            is_used=token.is_used,
            is_revoked=token.is_revoked,
            note=token.note,
            invite_url=build_invite_url(token.token)
        )
        for token in tokens
    ]
    
    # Refresh user to get updated quota
    db.refresh(current_user)
    
    return InviteCreateResponse(
        tokens=token_responses,
        remaining_quota=current_user.invites_available
    )


@router.get("/my-invites", response_model=InviteListResponse)
async def get_my_invites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all invite tokens created by current user.
    
    Returns list of tokens with usage status.
    """
    invite_service = InviteService(db)
    
    tokens = invite_service.get_user_tokens(current_user.id)
    
    token_responses = [
        InviteTokenResponse(
            id=str(token.id),
            token=token.token,
            created_at=token.created_at,
            expires_at=token.expires_at,
            is_used=token.is_used,
            is_revoked=token.is_revoked,
            note=token.note,
            invite_url=build_invite_url(token.token)
        )
        for token in tokens
    ]
    
    used_count = sum(1 for t in tokens if t.is_used)
    available_count = sum(1 for t in tokens if t.is_valid)
    
    return InviteListResponse(
        tokens=token_responses,
        total=len(tokens),
        used_count=used_count,
        available_count=available_count
    )


@router.get("/validate/{token}", response_model=InviteValidateResponse)
async def validate_invite(
    token: str = Path(..., description="Invite token to validate"),
    db: Session = Depends(get_db)
):
    """
    Validate an invite token (public endpoint - no auth required).
    
    Returns whether the token is valid and basic information.
    """
    invite_service = InviteService(db)
    
    invite_token = invite_service.validate_token(token)
    
    if not invite_token:
        return InviteValidateResponse(
            valid=False,
            reason="Token not found or invalid"
        )
    
    if not invite_token.is_valid:
        reason = "Token is "
        if invite_token.is_used:
            reason += "already used"
        elif invite_token.is_revoked:
            reason += "revoked"
        elif invite_token.is_expired:
            reason += "expired"
        else:
            reason += "invalid"
        
        return InviteValidateResponse(
            valid=False,
            reason=reason,
            created_by=invite_token.creator.username if invite_token.creator else None
        )
    
    return InviteValidateResponse(
        valid=True,
        created_by=invite_token.creator.username if invite_token.creator else None,
        expires_at=invite_token.expires_at
    )


@router.post("/revoke/{token_id}", response_model=InviteRevokeResponse)
async def revoke_invite(
    token_id: UUID,
    request: InviteRevokeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke an invite token.
    
    Can only revoke tokens you created (or admin can revoke any).
    Credits back to quota if not expired.
    """
    invite_service = InviteService(db)
    
    # Capture metadata
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    token = invite_service.revoke_token(
        token_id=token_id,
        user=current_user,
        reason=request.reason,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    # Check if it was credited back
    credited_back = not token.is_expired
    
    return InviteRevokeResponse(
        success=True,
        message="Invite token revoked successfully",
        credited_back=credited_back
    )

