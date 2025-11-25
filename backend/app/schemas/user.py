"""
User and tree schemas for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserPublicProfile(BaseModel):
    """Public user profile (limited information)."""
    id: str
    username: str
    created_at: datetime
    status: str
    is_core_member: bool
    
    class Config:
        from_attributes = True


class UserProfile(UserPublicProfile):
    """Extended user profile (for authenticated user viewing their own)."""
    email: str
    role: str
    invite_quota: int
    invites_used: int
    invites_available: int
    
    class Config:
        from_attributes = True


class TreeNode(BaseModel):
    """Recursive tree node for invite tree visualization."""
    id: str
    username: str
    status: str
    created_at: datetime
    depth: int
    health_score: Optional[float] = None
    maturity_level: Optional[str] = None
    children_count: int = 0
    children: List['TreeNode'] = []
    
    class Config:
        from_attributes = True


# Enable forward reference for recursive model
TreeNode.model_rebuild()


class UserTreeResponse(BaseModel):
    """Response schema for user's invite tree."""
    root_user_id: str
    tree: TreeNode
    total_descendants: int
    max_depth: int


class AncestorNode(BaseModel):
    """Node in the ancestor path (path to root)."""
    id: str
    username: str
    status: str
    created_at: datetime
    hops_to_root: int
    
    class Config:
        from_attributes = True


class UserAncestorsResponse(BaseModel):
    """Response schema for user's ancestors (path to root)."""
    user_id: str
    ancestors: List[AncestorNode]
    depth_from_root: int


class UserStatsResponse(BaseModel):
    """Response schema for user statistics."""
    direct_invites: int
    total_descendants: int
    active_descendants: int
    flagged_descendants: int
    banned_descendants: int
    current_health_score: Optional[float]
    maturity_level: str

