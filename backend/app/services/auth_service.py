"""
Authentication service for user registration, login, and token management.
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.auth import RefreshToken
from app.services.password_service import password_service
from app.services.token_service import token_service


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: Session):
        """
        Initialize auth service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Register a new user.
        
        Args:
            email: User email
            password: Plain text password
            full_name: Optional full name
            
        Returns:
            Created user
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = password_service.hash_password(password)
        
        # Create user
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.USER
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not password_service.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def create_tokens(
        self,
        user: User,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Create access and refresh tokens for a user.
        
        Args:
            user: User to create tokens for
            user_agent: Optional user agent string
            ip_address: Optional IP address
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        # Create access token
        access_token = token_service.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })
        
        # Create refresh token
        refresh_token_str = token_service.create_refresh_token({
            "sub": str(user.id)
        })
        
        # Store refresh token in database
        refresh_token = RefreshToken(
            token=refresh_token_str,
            user_id=user.id,
            expires_at=token_service.get_refresh_token_expiry(),
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        self.db.add(refresh_token)
        self.db.commit()
        
        return access_token, refresh_token_str
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create a new access token using a refresh token.
        
        Args:
            refresh_token: Refresh token string
            
        Returns:
            New access token if valid, None otherwise
        """
        # Decode refresh token
        payload = token_service.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # Check if token exists and is not revoked
        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not token_record:
            return None
        
        # Get user
        user = self.db.query(User).filter(User.id == token_record.user_id).first()
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token = token_service.create_access_token({
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        })
        
        return access_token
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if revoked, False if not found
        """
        token_record = self.db.query(RefreshToken).filter(
            RefreshToken.token == refresh_token
        ).first()
        
        if not token_record:
            return False
        
        token_record.is_revoked = True
        token_record.revoked_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of tokens revoked
        """
        result = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.utcnow()
        })
        
        self.db.commit()
        return result
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User if found, None otherwise
        """
        return self.db.query(User).filter(User.id == user_id).first()
