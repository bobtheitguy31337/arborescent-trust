"""
Admin API endpoints - requires admin role.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.schemas.admin import (
    AdminStatsResponse,
    UserFlagRequest,
    UserFlagResponse,
    PruneRequest,
    PruneResponse,
    PruneHistoryResponse,
    PruneHistoryItem,
    AuditLogResponse,
    AuditLogEntry,
    UserDetailedResponse,
    QuotaAdjustRequest,
    QuotaAdjustResponse,
    AffectedUserSummary
)
from app.models.user import User
from app.models.invite_token import InviteToken
from app.models.health_score import UserHealthScore
from app.models.audit_log import InviteAuditLog
from app.services.prune_service import PruneService
from app.services.tree_service import TreeService
from app.core.dependencies import require_admin
from app.core.exceptions import not_found_error


router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics.
    
    Requires admin role.
    """
    # User counts
    total_users = db.query(User).filter(User.deleted_at == None).count()
    active_users = db.query(User).filter(User.status == "active", User.deleted_at == None).count()
    flagged_users = db.query(User).filter(User.status == "flagged", User.deleted_at == None).count()
    banned_users = db.query(User).filter(User.status == "banned", User.deleted_at == None).count()
    suspended_users = db.query(User).filter(User.status == "suspended", User.deleted_at == None).count()
    deleted_users = db.query(User).filter(User.deleted_at != None).count()
    
    # Invite stats
    total_invites = db.query(InviteToken).count()
    used_invites = db.query(InviteToken).filter(InviteToken.is_used == True).count()
    
    # Health score average
    avg_health = db.query(func.avg(UserHealthScore.overall_health)).scalar() or 0.0
    
    # Low health users
    low_health = db.query(UserHealthScore).filter(
        UserHealthScore.overall_health < 50
    ).count()
    
    # Recent registrations
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    recent_24h = db.query(User).filter(
        User.created_at >= day_ago,
        User.deleted_at == None
    ).count()
    
    recent_7d = db.query(User).filter(
        User.created_at >= week_ago,
        User.deleted_at == None
    ).count()
    
    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        flagged_users=flagged_users,
        banned_users=banned_users,
        suspended_users=suspended_users,
        deleted_users=deleted_users,
        total_invites_issued=total_invites,
        total_invites_used=used_invites,
        avg_health_score=float(avg_health),
        low_health_users=low_health,
        recent_registrations_24h=recent_24h,
        recent_registrations_7d=recent_7d
    )


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filters.
    
    - **page**: Page number (default 1)
    - **page_size**: Results per page (default 50, max 100)
    - **status**: Filter by status (active, flagged, banned, suspended)
    - **search**: Search by username or email
    """
    query = db.query(User).filter(User.deleted_at == None)
    
    if status:
        query = query.filter(User.status == status)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) | (User.email.ilike(search_term))
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    
    users = query.offset(offset).limit(page_size).all()
    
    return {
        "users": [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "status": u.status,
                "role": u.role,
                "created_at": u.created_at.isoformat()
            }
            for u in users
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }


@router.get("/users/{user_id}", response_model=UserDetailedResponse)
async def get_user_detailed(
    user_id: UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed user information.
    
    Includes forensic data and health scores.
    """
    tree_service = TreeService(db)
    user = tree_service.get_user_or_404(user_id)
    
    # Get invited by username
    invited_by_username = None
    if user.invited_by_user_id:
        invited_by = db.query(User).filter(User.id == user.invited_by_user_id).first()
        if invited_by:
            invited_by_username = invited_by.username
    
    # Get health score
    health_record = db.query(UserHealthScore).filter(
        UserHealthScore.user_id == user_id
    ).order_by(UserHealthScore.calculated_at.desc()).first()
    
    # Get stats
    stats = tree_service.get_subtree_stats(user_id)
    
    return UserDetailedResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role,
        status=user.status,
        is_core_member=user.is_core_member,
        invite_quota=user.invite_quota,
        invites_used=user.invites_used,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
        invited_by_user_id=str(user.invited_by_user_id) if user.invited_by_user_id else None,
        invited_by_username=invited_by_username,
        registration_ip=str(user.registration_ip) if user.registration_ip else None,
        registration_user_agent=user.registration_user_agent,
        registration_fingerprint=user.registration_fingerprint,
        deleted_at=user.deleted_at,
        deleted_reason=user.deleted_reason,
        current_health_score=float(health_record.overall_health) if health_record else None,
        maturity_level=health_record.maturity_level if health_record else "branch",
        direct_invites_count=stats["direct_invites"],
        total_descendants=stats["total_descendants"]
    )


@router.post("/users/{user_id}/flag", response_model=UserFlagResponse)
async def flag_user(
    user_id: UUID,
    request: UserFlagRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Flag a user for review.
    
    Changes user status to 'flagged'.
    """
    tree_service = TreeService(db)
    user = tree_service.get_user_or_404(user_id)
    
    old_status = user.status
    user.status = "flagged"
    
    # Log to audit
    audit_entry = InviteAuditLog(
        event_type="user_flagged",
        actor_user_id=current_admin.id,
        target_user_id=user.id,
        event_data={
            "reason": request.reason,
            "old_status": old_status
        }
    )
    db.add(audit_entry)
    
    db.commit()
    
    return UserFlagResponse(
        success=True,
        message=f"User {user.username} flagged for review",
        user_id=str(user.id),
        new_status="flagged"
    )


@router.post("/users/{user_id}/unflag", response_model=UserFlagResponse)
async def unflag_user(
    user_id: UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Remove flag from user (set back to active).
    """
    tree_service = TreeService(db)
    user = tree_service.get_user_or_404(user_id)
    
    old_status = user.status
    user.status = "active"
    
    # Log to audit
    audit_entry = InviteAuditLog(
        event_type="user_status_changed",
        actor_user_id=current_admin.id,
        target_user_id=user.id,
        event_data={
            "action": "unflagged",
            "old_status": old_status,
            "new_status": "active"
        }
    )
    db.add(audit_entry)
    
    db.commit()
    
    return UserFlagResponse(
        success=True,
        message=f"User {user.username} unflagged",
        user_id=str(user.id),
        new_status="active"
    )


@router.post("/prune", response_model=PruneResponse)
async def prune_branch(
    request: PruneRequest,
    http_request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Prune a branch (soft delete all descendants).
    
    - **root_user_id**: UUID of root user to prune
    - **reason**: Detailed reason for pruning
    - **dry_run**: If true, preview affected users without executing
    
    This is a destructive operation that should be used carefully.
    """
    prune_service = PruneService(db)
    
    # Get affected users
    affected_users = prune_service.get_affected_users(UUID(request.root_user_id))
    
    if request.dry_run:
        # Preview mode
        affected_summaries = [
            AffectedUserSummary(
                id=u["id"],
                username=u["username"],
                email=u["email"],
                status=u["status"],
                created_at=u["created_at"],
                descendants_count=u["descendants_count"]
            )
            for u in affected_users
        ]
        
        return PruneResponse(
            dry_run=True,
            root_user_id=request.root_user_id,
            affected_count=len(affected_users),
            affected_users=affected_summaries
        )
    
    # Execute prune
    client_ip = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    operation = prune_service.execute_prune(
        root_user_id=UUID(request.root_user_id),
        reason=request.reason,
        executed_by_user_id=current_admin.id,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    return PruneResponse(
        dry_run=False,
        operation_id=str(operation.id),
        root_user_id=request.root_user_id,
        affected_count=operation.affected_user_count,
        status=operation.status,
        executed_at=operation.executed_at
    )


@router.get("/prune-history", response_model=PruneHistoryResponse)
async def get_prune_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get history of prune operations.
    """
    prune_service = PruneService(db)
    
    offset = (page - 1) * page_size
    operations = prune_service.get_prune_operations(limit=page_size, offset=offset)
    
    items = []
    for op in operations:
        root_user = db.query(User).filter(User.id == op.root_user_id).first()
        executed_by = db.query(User).filter(User.id == op.executed_by_user_id).first()
        
        items.append(PruneHistoryItem(
            id=str(op.id),
            root_user_id=str(op.root_user_id),
            root_username=root_user.username if root_user else "Unknown",
            affected_count=op.affected_user_count,
            reason=op.reason,
            executed_by_username=executed_by.username if executed_by else "Unknown",
            status=op.status,
            created_at=op.created_at,
            executed_at=op.executed_at
        ))
    
    from app.models.prune_operation import PruneOperation
    total = db.query(PruneOperation).count()
    
    return PruneHistoryResponse(
        operations=items,
        total=total
    )


@router.get("/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit log entries.
    
    - **page**: Page number
    - **page_size**: Results per page
    - **event_type**: Filter by event type
    """
    query = db.query(InviteAuditLog)
    
    if event_type:
        query = query.filter(InviteAuditLog.event_type == event_type)
    
    total = query.count()
    offset = (page - 1) * page_size
    
    entries = query.order_by(InviteAuditLog.created_at.desc()).offset(offset).limit(page_size).all()
    
    audit_entries = []
    for entry in entries:
        actor = db.query(User).filter(User.id == entry.actor_user_id).first() if entry.actor_user_id else None
        target = db.query(User).filter(User.id == entry.target_user_id).first() if entry.target_user_id else None
        
        audit_entries.append(AuditLogEntry(
            id=entry.id,
            event_type=entry.event_type,
            actor_username=actor.username if actor else None,
            target_username=target.username if target else None,
            event_data=entry.event_data,
            created_at=entry.created_at,
            ip_address=str(entry.ip_address) if entry.ip_address else None
        ))
    
    return AuditLogResponse(
        logs=audit_entries,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/quota/adjust", response_model=QuotaAdjustResponse)
async def adjust_user_quota(
    request: QuotaAdjustRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Adjust a user's invite quota.
    
    - **user_id**: User to adjust
    - **new_quota**: New quota value
    - **reason**: Reason for adjustment
    """
    tree_service = TreeService(db)
    user = tree_service.get_user_or_404(UUID(request.user_id))
    
    old_quota = user.invite_quota
    user.invite_quota = request.new_quota
    
    # Log to audit
    audit_entry = InviteAuditLog(
        event_type="quota_adjusted",
        actor_user_id=current_admin.id,
        target_user_id=user.id,
        event_data={
            "old_quota": old_quota,
            "new_quota": request.new_quota,
            "reason": request.reason
        }
    )
    db.add(audit_entry)
    
    db.commit()
    
    return QuotaAdjustResponse(
        success=True,
        user_id=str(user.id),
        old_quota=old_quota,
        new_quota=request.new_quota,
        message=f"Quota adjusted for {user.username}"
    )

