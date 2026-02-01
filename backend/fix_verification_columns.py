"""
Script to add verification columns to users table if they don't exist.
Safe to run multiple times - checks existence before adding.
"""
import sys
import os
from sqlalchemy import inspect, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine

def add_verification_columns():
    """Add verification columns if they don't exist."""
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            print(f"Current users table columns: {columns}")
            
            changes_made = False
            
            # Add verification_token if it doesn't exist
            if 'verification_token' not in columns:
                print("Adding verification_token column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)"))
                conn.commit()
                print("✓ Added verification_token column")
                changes_made = True
            else:
                print("✓ verification_token column already exists")
            
            # Add verification_token_expires if it doesn't exist
            if 'verification_token_expires' not in columns:
                print("Adding verification_token_expires column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN verification_token_expires TIMESTAMP WITH TIME ZONE"))
                conn.commit()
                print("✓ Added verification_token_expires column")
                changes_made = True
            else:
                print("✓ verification_token_expires column already exists")
            
            if changes_made:
                print("\n✓ Database schema updated successfully!")
            else:
                print("\n✓ Database schema is up to date - no changes needed")
                
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        raise

if __name__ == "__main__":
    add_verification_columns()
