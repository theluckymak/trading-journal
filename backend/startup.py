"""
Startup script that runs database migrations before starting the server.
"""
import os
import sys
import subprocess

def fix_verification_columns():
    """Add verification columns if they don't exist."""
    print("=" * 60)
    print("Checking verification columns...")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["python", "fix_verification_columns.py"],
            check=True,
            capture_output=False,
            text=True
        )
        print("=" * 60)
        print("✓ Verification columns check completed!")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"✗ Verification fix failed: {e}")
        print("Continuing with migrations anyway...")
        print("=" * 60)

def run_migrations():
    """Run alembic migrations."""
    print("=" * 60)
    print("Running database migrations...")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=False,
            text=True
        )
        print("=" * 60)
        print("✓ Migrations completed successfully!")
        print("=" * 60)
    except subprocess.CalledProcessError as e:
        print("=" * 60)
        print(f"✗ Migration failed: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        print("Continuing with application startup...")
        print("=" * 60)

def start_server():
    """Start the uvicorn server."""
    port = os.environ.get("PORT", "8000")
    print(f"Starting FastAPI server on port {port}...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(port)])

if __name__ == "__main__":
    fix_verification_columns()
    run_migrations()
    start_server()
