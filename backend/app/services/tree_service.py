"""
Tree service - handles graph traversal and tree operations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import UUID

from app.models.user import User
from app.core.exceptions import not_found_error


class TreeService:
    """Service for invite tree operations and graph traversal."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_or_404(self, user_id: UUID) -> User:
        """Get user by ID or raise 404."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise not_found_error("User not found")
        return user
    
    def get_descendants(self, root_user_id: UUID, max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all descendants of a user using recursive CTE.
        
        Args:
            root_user_id: UUID of root user
            max_depth: Optional maximum depth to traverse
            
        Returns:
            List of dicts containing descendant information
        """
        query = text("""
            WITH RECURSIVE subtree AS (
                -- Base case: start with the root user
                SELECT 
                    id,
                    username,
                    email,
                    status,
                    invited_by_user_id,
                    created_at,
                    0 as depth,
                    ARRAY[id] as path
                FROM users
                WHERE id = :root_user_id
                  AND deleted_at IS NULL
                
                UNION ALL
                
                -- Recursive case: get children
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.status,
                    u.invited_by_user_id,
                    u.created_at,
                    st.depth + 1,
                    st.path || u.id
                FROM users u
                INNER JOIN subtree st ON u.invited_by_user_id = st.id
                WHERE u.deleted_at IS NULL
                  AND (:max_depth IS NULL OR st.depth < :max_depth)
            )
            SELECT * FROM subtree
            ORDER BY depth, created_at;
        """)
        
        result = self.db.execute(
            query,
            {"root_user_id": str(root_user_id), "max_depth": max_depth}
        )
        
        descendants = []
        for row in result:
            descendants.append({
                "id": str(row.id),
                "username": row.username,
                "email": row.email,
                "status": row.status,
                "invited_by_user_id": str(row.invited_by_user_id) if row.invited_by_user_id else None,
                "created_at": row.created_at,
                "depth": row.depth,
                "path": [str(p) for p in row.path]
            })
        
        return descendants
    
    def get_ancestors(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all ancestors of a user (path to root).
        
        Args:
            user_id: UUID of user
            
        Returns:
            List of dicts containing ancestor information
        """
        query = text("""
            WITH RECURSIVE ancestors AS (
                -- Base case: start with the user
                SELECT 
                    id,
                    username,
                    email,
                    status,
                    invited_by_user_id,
                    created_at,
                    0 as hops_to_root
                FROM users
                WHERE id = :user_id
                
                UNION ALL
                
                -- Recursive case: climb up
                SELECT 
                    u.id,
                    u.username,
                    u.email,
                    u.status,
                    u.invited_by_user_id,
                    u.created_at,
                    a.hops_to_root + 1
                FROM users u
                INNER JOIN ancestors a ON a.invited_by_user_id = u.id
            )
            SELECT * FROM ancestors
            ORDER BY hops_to_root DESC;
        """)
        
        result = self.db.execute(query, {"user_id": str(user_id)})
        
        ancestors = []
        for row in result:
            ancestors.append({
                "id": str(row.id),
                "username": row.username,
                "email": row.email,
                "status": row.status,
                "invited_by_user_id": str(row.invited_by_user_id) if row.invited_by_user_id else None,
                "created_at": row.created_at,
                "hops_to_root": row.hops_to_root
            })
        
        return ancestors
    
    def get_subtree_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get statistics about a user's subtree.
        
        Args:
            user_id: UUID of user
            
        Returns:
            Dict with subtree statistics
        """
        descendants = self.get_descendants(user_id)
        
        if not descendants:
            return {
                "total_descendants": 0,
                "active_count": 0,
                "flagged_count": 0,
                "banned_count": 0,
                "suspended_count": 0,
                "max_depth": 0,
                "direct_invites": 0
            }
        
        # Calculate stats
        total = len(descendants) - 1  # Exclude root user
        active = sum(1 for d in descendants if d["status"] == "active") - 1
        flagged = sum(1 for d in descendants if d["status"] == "flagged")
        banned = sum(1 for d in descendants if d["status"] == "banned")
        suspended = sum(1 for d in descendants if d["status"] == "suspended")
        max_depth = max(d["depth"] for d in descendants)
        direct_invites = sum(1 for d in descendants if d["depth"] == 1)
        
        return {
            "total_descendants": total,
            "active_count": active,
            "flagged_count": flagged,
            "banned_count": banned,
            "suspended_count": suspended,
            "max_depth": max_depth,
            "direct_invites": direct_invites
        }
    
    def build_tree_structure(self, root_user_id: UUID, max_depth: int = 5) -> Dict[str, Any]:
        """
        Build a nested tree structure for visualization.
        
        Args:
            root_user_id: UUID of root user
            max_depth: Maximum depth to include
            
        Returns:
            Nested dict representing the tree
        """
        descendants = self.get_descendants(root_user_id, max_depth)
        
        if not descendants:
            raise not_found_error("User not found")
        
        # Build lookup dict
        nodes = {d["id"]: {**d, "children": []} for d in descendants}
        
        # Build tree structure
        root = None
        for node_id, node in nodes.items():
            if node["invited_by_user_id"] and node["invited_by_user_id"] in nodes:
                parent = nodes[node["invited_by_user_id"]]
                parent["children"].append(node)
            else:
                root = node
        
        return root
    
    def get_direct_invitees(self, user_id: UUID) -> List[User]:
        """
        Get users directly invited by a user.
        
        Args:
            user_id: UUID of user
            
        Returns:
            List of User objects
        """
        return self.db.query(User).filter(
            User.invited_by_user_id == user_id,
            User.deleted_at == None
        ).order_by(User.created_at.desc()).all()

