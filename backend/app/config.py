"""
Application configuration management.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = "postgresql://trading_user:trading_password@localhost:5432/trading_journal"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str = "dev-secret-key-b8f5e9c2d7a1f3e8c4b6a9d2e7f1c3a8b5d9e2f7c1a4b8d3e9f2c7a1d5b8e3f9"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Encryption for sensitive data (MT5 credentials)
    ENCRYPTION_KEY: str = "dev-encryption-key-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS - can be overridden in .env
    # For production, set: CORS_ORIGINS=https://maktrades.app,https://your-api-domain.railway.app
    # For Railway, this MUST be set in environment variables, not defaults
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000,https://maktrades.app"
    
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Parse CORS_ORIGINS string into list and validate."""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        # Log CORS origins for security audit (don't expose in production logs)
        if self.DEBUG:
            print(f"CORS allowed origins: {origins}")
        return origins
    
    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = ""  # Optional, defaults to SMTP_USER
    
    @property
    def get_from_email(self) -> str:
        """Get the from email, defaulting to SMTP_USER if not set."""
        return self.FROM_EMAIL if self.FROM_EMAIL else self.SMTP_USER
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
