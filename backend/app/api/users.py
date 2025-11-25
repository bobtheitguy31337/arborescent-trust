"""
User and tree API endpoints.
"""

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.user import (
    UserProfile,
    UserPublicProfile,
    UserTreeResponse,
    UserAncestorsResponse,
    UserStatsResponse,
    TreeNode,
    AncestorNode
)
from app.services.tree_service import TreeService
from app.services.health_service import HealthService
from app.core.dependencies import get_current_user, get_optional_user
from app.core.exceptions import forbidden_error
from app.models.user import User


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserProfile)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserProfile(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        status=current_user.status,
        is_core_member=current_user.is_core_member,
        role=current_user.role,
        invite_quota=current_user.invite_quota,
        invites_used=current_user.invites_used,
        invites_available=current_user.invites_available
    )


@router.get("/{user_identifier}", response_model=UserPublicProfile)
async def get_user_profile(
    user_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """
    Get public user profile.
    
    - **user_identifier**: User ID (UUID), username, or email
    
    Returns limited information for privacy.
    """
    # Look up user by ID, username, or email
    try:
        user_id = UUID(user_identifier)
        user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    except ValueError:
        # Not a UUID, try username or email
        user = db.query(User).filter(
            ((User.username == user_identifier) | (User.email == user_identifier)),
            User.deleted_at == None
        ).first()
    
    if not user:
        raise not_found_error("User not found")
    
    return UserPublicProfile(
        id=str(user.id),
        username=user.username,
        created_at=user.created_at,
        status=user.status,
        is_core_member=user.is_core_member
    )


@router.get("/{user_identifier}/tree", response_model=UserTreeResponse)
async def get_user_tree(
    user_identifier: str,
    max_depth: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get invite tree for a user (their descendants).
    
    - **user_identifier**: User ID (UUID), username, or email
    - **max_depth**: Maximum depth to include (default 5)
    
    Users can only view their own tree unless they're an admin.
    """
    # Look up user by ID, username, or email
    try:
        user_id = UUID(user_identifier)
        target_user = db.query(User).filter(User.id == user_id).first()
    except ValueError:
        # Not a UUID, try username or email
        target_user = db.query(User).filter(
            (User.username == user_identifier) | (User.email == user_identifier)
        ).first()
    
    if not target_user:
        raise not_found_error("User not found")
    
    user_id = target_user.id
    
    # Privacy check
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise forbidden_error("Can only view your own tree")
    
    tree_service = TreeService(db)
    health_service = HealthService(db)
    
    # Build tree structure
    tree_data = tree_service.build_tree_structure(user_id, max_depth)
    
    if not tree_data:
        raise forbidden_error("Tree not found")
    
    # Get health scores for nodes
    def add_health_scores(node):
        health_record = health_service.get_latest_health_score(UUID(node["id"]))
        if health_record:
            node["health_score"] = float(health_record.overall_health)
            node["maturity_level"] = health_record.maturity_level
        else:
            node["health_score"] = None
            node["maturity_level"] = "branch"
        
        node["children_count"] = len(node["children"])
        
        for child in node["children"]:
            add_health_scores(child)
    
    add_health_scores(tree_data)
    
    # Convert to TreeNode
    def dict_to_tree_node(data) -> TreeNode:
        children = [dict_to_tree_node(child) for child in data.get("children", [])]
        return TreeNode(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            status=data["status"],
            created_at=data["created_at"],
            depth=data["depth"],
            health_score=data.get("health_score"),
            maturity_level=data.get("maturity_level"),
            children_count=data["children_count"],
            children=children
        )
    
    tree_node = dict_to_tree_node(tree_data)
    
    # Get total descendants
    stats = tree_service.get_subtree_stats(user_id)
    
    return UserTreeResponse(
        root_user_id=str(user_id),
        tree=tree_node,
        total_descendants=stats["total_descendants"],
        max_depth=stats["max_depth"]
    )


@router.get("/{user_id}/ancestors", response_model=UserAncestorsResponse)
async def get_user_ancestors(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get path to root (all ancestors).
    
    Shows the invite chain from user to root.
    """
    # Privacy check
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise forbidden_error("Can only view your own ancestry")
    
    tree_service = TreeService(db)
    
    ancestors_data = tree_service.get_ancestors(user_id)
    
    ancestors = [
        AncestorNode(
            id=a["id"],
            username=a["username"],
            status=a["status"],
            created_at=a["created_at"],
            hops_to_root=a["hops_to_root"]
        )
        for a in ancestors_data
    ]
    
    depth = max(a.hops_to_root for a in ancestors) if ancestors else 0
    
    return UserAncestorsResponse(
        user_id=str(user_id),
        ancestors=ancestors,
        depth_from_root=depth
    )


@router.get("/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about a user's invite tree.
    
    Users can only view their own stats unless they're an admin.
    """
    # Privacy check
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise forbidden_error("Can only view your own stats")
    
    tree_service = TreeService(db)
    health_service = HealthService(db)
    
    stats = tree_service.get_subtree_stats(user_id)
    health_record = health_service.get_latest_health_score(user_id)
    
    return UserStatsResponse(
        direct_invites=stats["direct_invites"],
        total_descendants=stats["total_descendants"],
        active_descendants=stats["active_count"],
        flagged_descendants=stats["flagged_count"],
        banned_descendants=stats["banned_count"],
        current_health_score=float(health_record.overall_health) if health_record else None,
        maturity_level=health_record.maturity_level if health_record else "branch"
    )

