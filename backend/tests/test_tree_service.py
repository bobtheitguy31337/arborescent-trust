"""
Tests for tree service functionality.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.services.tree_service import TreeService
from app.models.user import User
from app.database import SessionLocal


@pytest.fixture
def db():
    """Create database session for testing."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_tree(db):
    """
    Create a sample invite tree for testing:
    
        root
        ├── child1
        │   ├── grandchild1
        │   └── grandchild2
        └── child2
    """
    # Create root user
    root = User(
        id=uuid4(),
        email="root@example.com",
        username="root",
        password_hash="dummy",
        is_core_member=True,
        status="active",
        invite_quota=100
    )
    db.add(root)
    db.flush()
    
    # Create children
    child1 = User(
        id=uuid4(),
        email="child1@example.com",
        username="child1",
        password_hash="dummy",
        invited_by_user_id=root.id,
        status="active"
    )
    child2 = User(
        id=uuid4(),
        email="child2@example.com",
        username="child2",
        password_hash="dummy",
        invited_by_user_id=root.id,
        status="active"
    )
    db.add_all([child1, child2])
    db.flush()
    
    # Create grandchildren
    grandchild1 = User(
        id=uuid4(),
        email="grandchild1@example.com",
        username="grandchild1",
        password_hash="dummy",
        invited_by_user_id=child1.id,
        status="active"
    )
    grandchild2 = User(
        id=uuid4(),
        email="grandchild2@example.com",
        username="grandchild2",
        password_hash="dummy",
        invited_by_user_id=child1.id,
        status="flagged"
    )
    db.add_all([grandchild1, grandchild2])
    
    db.commit()
    
    return {
        "root": root,
        "child1": child1,
        "child2": child2,
        "grandchild1": grandchild1,
        "grandchild2": grandchild2
    }


def test_get_descendants(db, sample_tree):
    """Test getting all descendants of a user."""
    tree_service = TreeService(db)
    root = sample_tree["root"]
    
    descendants = tree_service.get_descendants(root.id)
    
    # Should include root + 4 descendants = 5 total
    assert len(descendants) == 5
    
    # Check depths
    root_node = next(d for d in descendants if d["username"] == "root")
    assert root_node["depth"] == 0
    
    child_nodes = [d for d in descendants if d["username"].startswith("child")]
    assert all(d["depth"] == 1 for d in child_nodes)
    
    grandchild_nodes = [d for d in descendants if d["username"].startswith("grandchild")]
    assert all(d["depth"] == 2 for d in grandchild_nodes)


def test_get_ancestors(db, sample_tree):
    """Test getting path to root."""
    tree_service = TreeService(db)
    grandchild1 = sample_tree["grandchild1"]
    
    ancestors = tree_service.get_ancestors(grandchild1.id)
    
    # Should include grandchild1, child1, root = 3 total
    assert len(ancestors) == 3
    
    # Check path order (should be root -> child1 -> grandchild1)
    assert ancestors[0]["username"] == "root"
    assert ancestors[1]["username"] == "child1"
    assert ancestors[2]["username"] == "grandchild1"
    
    # Check hops to root
    assert ancestors[0]["hops_to_root"] == 2
    assert ancestors[1]["hops_to_root"] == 1
    assert ancestors[2]["hops_to_root"] == 0


def test_get_subtree_stats(db, sample_tree):
    """Test subtree statistics calculation."""
    tree_service = TreeService(db)
    root = sample_tree["root"]
    
    stats = tree_service.get_subtree_stats(root.id)
    
    assert stats["total_descendants"] == 4  # Excludes root
    assert stats["active_count"] == 3  # child1, child2, grandchild1
    assert stats["flagged_count"] == 1  # grandchild2
    assert stats["banned_count"] == 0
    assert stats["max_depth"] == 2
    assert stats["direct_invites"] == 2  # child1, child2


def test_build_tree_structure(db, sample_tree):
    """Test building nested tree structure."""
    tree_service = TreeService(db)
    root = sample_tree["root"]
    
    tree = tree_service.build_tree_structure(root.id)
    
    assert tree["username"] == "root"
    assert len(tree["children"]) == 2
    
    # Find child1 in children
    child1 = next(c for c in tree["children"] if c["username"] == "child1")
    assert len(child1["children"]) == 2
    
    # Check grandchildren
    grandchild_usernames = [gc["username"] for gc in child1["children"]]
    assert "grandchild1" in grandchild_usernames
    assert "grandchild2" in grandchild_usernames


def test_get_direct_invitees(db, sample_tree):
    """Test getting users directly invited by a user."""
    tree_service = TreeService(db)
    child1 = sample_tree["child1"]
    
    invitees = tree_service.get_direct_invitees(child1.id)
    
    assert len(invitees) == 2
    usernames = [user.username for user in invitees]
    assert "grandchild1" in usernames
    assert "grandchild2" in usernames


def test_soft_delete_exclusion(db, sample_tree):
    """Test that soft-deleted users are excluded from tree queries."""
    tree_service = TreeService(db)
    root = sample_tree["root"]
    grandchild1 = sample_tree["grandchild1"]
    
    # Soft delete grandchild1
    grandchild1.deleted_at = datetime.utcnow()
    grandchild1.status = "banned"
    db.commit()
    
    # Get descendants again
    descendants = tree_service.get_descendants(root.id)
    
    # Should not include soft-deleted grandchild1
    usernames = [d["username"] for d in descendants]
    assert "grandchild1" not in usernames
    assert "grandchild2" in usernames  # Other grandchild should still be there
    
    # Should now be 4 users instead of 5
    assert len(descendants) == 4

