"""
Script to create the initial admin user and generate invite tokens.
"""

import sys
from uuid import uuid4

from app.database import SessionLocal
from app.models.user import User
from app.models.invite_token import InviteToken
from app.core.security import hash_password, generate_secure_token
from app.config import settings
from datetime import datetime, timedelta


def create_admin():
    """Create initial admin user."""
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == settings.INITIAL_ADMIN_EMAIL).first()
        if existing_admin:
            print(f"❌ Admin user already exists: {existing_admin.email}")
            return
        
        # Create admin user
        admin = User(
            id=uuid4(),
            email=settings.INITIAL_ADMIN_EMAIL,
            username="admin",
            password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
            is_core_member=True,
            role="superadmin",
            invite_quota=1000,  # High quota for admin
            invites_used=0,
            status="active",
            invited_by_user_id=None  # Root user
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   Password: {settings.INITIAL_ADMIN_PASSWORD}")
        print(f"   Role: {admin.role}")
        print()
        
        # Generate some initial invite tokens
        print("🎟️  Generating 5 initial invite tokens...")
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        tokens = []
        for i in range(5):
            token = InviteToken(
                token=generate_secure_token(),
                created_by_user_id=admin.id,
                expires_at=expires_at,
                note=f"Initial invite token {i+1}"
            )
            db.add(token)
            tokens.append(token)
        
        admin.invites_used += 5
        
        db.commit()
        
        print("\n📋 Initial Invite Tokens:")
        for i, token in enumerate(tokens, 1):
            print(f"   {i}. {token.token}")
        
        print("\n⚠️  IMPORTANT: Save these tokens securely! They won't be shown again.")
        print("   Use these tokens to create the first non-admin users.")
        print()
        print("🚀 Setup complete! You can now:")
        print("   1. Login as admin with the credentials above")
        print("   2. Use the invite tokens to register new users")
        print("   3. Access the API docs at http://localhost:8000/docs")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 Creating initial admin user...")
    create_admin()

