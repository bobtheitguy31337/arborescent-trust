"""
Admin schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AdminStatsResponse(BaseModel):
    """Response schema for admin dashboard statistics."""
    total_users: int
    active_users: int
    flagged_users: int
    banned_users: int
    suspended_users: int
    deleted_users: int
    total_invites_issued: int
    total_invites_used: int
    avg_health_score: float
    low_health_users: int
    recent_registrations_24h: int
    recent_registrations_7d: int


class UserFlagRequest(BaseModel):
    """Request schema for flagging a user."""
    reason: str = Field(..., min_length=10, max_length=1000)


class UserFlagResponse(BaseModel):
    """Response schema for user flagging."""
    success: bool
    message: str
    user_id: str
    new_status: str


class PruneRequest(BaseModel):
    """Request schema for pruning a branch."""
    root_user_id: str
    reason: str = Field(..., min_length=20, max_length=2000)
    dry_run: bool = False


class AffectedUserSummary(BaseModel):
    """Summary of an affected user in prune operation."""
    id: str
    username: str
    email: str
    status: str
    created_at: str
    descendants_count: int


class PruneResponse(BaseModel):
    """Response schema for prune operation."""
    dry_run: bool
    operation_id: Optional[str] = None
    root_user_id: str
    affected_count: int
    affected_users: Optional[List[AffectedUserSummary]] = None
    status: Optional[str] = None
    executed_at: Optional[datetime] = None


class PruneHistoryItem(BaseModel):
    """Item in prune history list."""
    id: str
    root_user_id: str
    root_username: str
    affected_count: int
    reason: str
    executed_by_username: str
    status: str
    created_at: datetime
    executed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PruneHistoryResponse(BaseModel):
    """Response schema for prune history."""
    operations: List[PruneHistoryItem]
    total: int


class AuditLogEntry(BaseModel):
    """Single audit log entry."""
    id: int
    event_type: str
    actor_username: Optional[str]
    target_username: Optional[str]
    event_data: Dict[str, Any]
    created_at: datetime
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response schema for audit log."""
    logs: List[AuditLogEntry]
    total: int
    page: int
    page_size: int


class UserDetailedResponse(BaseModel):
    """Detailed user information for admin."""
    id: str
    username: str
    email: str
    role: str
    status: str
    is_core_member: bool
    invite_quota: int
    invites_used: int
    created_at: datetime
    last_login_at: Optional[datetime]
    invited_by_user_id: Optional[str]
    invited_by_username: Optional[str]
    registration_ip: Optional[str]
    registration_user_agent: Optional[str]
    registration_fingerprint: Optional[str]
    deleted_at: Optional[datetime]
    deleted_reason: Optional[str]
    current_health_score: Optional[float]
    maturity_level: Optional[str]
    direct_invites_count: int
    total_descendants: int
    
    class Config:
        from_attributes = True


class QuotaAdjustRequest(BaseModel):
    """Request schema for adjusting user quota."""
    user_id: str
    new_quota: int = Field(..., ge=0, le=1000)
    reason: str = Field(..., min_length=10, max_length=500)


class QuotaAdjustResponse(BaseModel):
    """Response schema for quota adjustment."""
    success: bool
    user_id: str
    old_quota: int
    new_quota: int
    message: str

