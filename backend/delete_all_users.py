"""
Script to delete all users from the database.
WARNING: This will permanently delete all users and their related data!
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User

def delete_all_users():
    """Delete all users from the database."""
    db = SessionLocal()
    try:
        # Get count before deletion
        user_count = db.query(User).count()
        
        if user_count == 0:
            print("No users found in the database.")
            return
        
        print(f"Found {user_count} user(s) in the database.")
        print("Deleting all users...")
        
        # Delete all users (cascade will handle related records)
        db.query(User).delete()
        db.commit()
        
        print(f"✓ Successfully deleted {user_count} user(s) and all their related data.")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error deleting users: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_users()
