"""
Startup script that runs database migrations before starting the server.
"""
import os
import sys
import subprocess

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
    print("Starting FastAPI server...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    run_migrations()
    start_server()
