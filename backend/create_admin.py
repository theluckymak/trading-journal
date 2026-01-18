"""
Script to create an admin user.
Run this from the backend directory: python create_admin.py
"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.services.password_service import PasswordService

def create_admin():
    """Create an admin user."""
    # Create database session
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        admin_email = "admin@trading-journal.com"
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            if existing_admin.role == UserRole.ADMIN:
                print(f"✓ Admin user already exists: {admin_email}")
                print(f"  Name: {existing_admin.full_name}")
                print(f"  Role: {existing_admin.role}")
                return
            else:
                # Upgrade existing user to admin
                existing_admin.role = UserRole.ADMIN
                db.commit()
                print(f"✓ Upgraded user to admin: {admin_email}")
                return
        
        # Create new admin user
        password = "Admin123!"  # Change this password after first login!
        password_service = PasswordService()
        hashed_password = password_service.hash_password(password)
        
        admin_user = User(
            email=admin_email,
            hashed_password=hashed_password,
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("\n" + "="*60)
        print("✓ Admin user created successfully!")
        print("="*60)
        print(f"Email:    {admin_email}")
        print(f"Password: {password}")
        print(f"Name:     {admin_user.full_name}")
        print(f"Role:     {admin_user.role}")
        print("="*60)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating admin user...\n")
    create_admin()
