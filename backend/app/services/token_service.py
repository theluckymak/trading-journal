"""
JWT token service for access and refresh tokens.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt

from app.config import settings


class TokenService:
    """Service for creating and validating JWT tokens."""
    
    def __init__(self):
        """Initialize token service with settings."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new access token.
        
        Args:
            data: Dictionary containing claims to encode (must include 'sub' for user_id)
            
        Returns:
            Encoded JWT access token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a new refresh token.
        
        Args:
            data: Dictionary containing claims to encode (must include 'sub' for user_id)
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def get_refresh_token_expiry(self) -> datetime:
        """Get expiry datetime for a refresh token."""
        return datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)


# Global instance
token_service = TokenService()
