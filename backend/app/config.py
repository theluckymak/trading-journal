"""
Application configuration management.
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Encryption for sensitive data (MT5 credentials)
    ENCRYPTION_KEY: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS - can be overridden in .env
    # For production, set: CORS_ORIGINS=https://maktrades.app,https://your-backend-domain.railway.app
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    
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
