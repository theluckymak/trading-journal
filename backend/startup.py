"""
Startup script that runs database migrations before starting the server.
"""
import os
import sys
import subprocess

def run_migrations():
    """Run alembic migrations."""
    print("Running database migrations...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Migrations completed successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        print(f"Error output: {e.stderr}")
        # Don't exit - let the app start anyway
        print("Continuing with application startup...")

def start_server():
    """Start the uvicorn server."""
    print("Starting FastAPI server...")
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    run_migrations()
    start_server()
