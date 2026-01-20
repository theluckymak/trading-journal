"""
Authentication middleware and dependencies.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.token_service import token_service
from app.services.auth_service import AuthService
from app.models.user import User
from app.utils.logging import get_logger, log_security_event

logger = get_logger(__name__)


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Decode token
    payload = token_service.decode_token(token)
    
    if not payload or payload.get("type") != "access":
        log_security_event("invalid_token", {"reason": "token_decode_failed"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(int(user_id))
    
    if not user:
        log_security_event("user_not_found", {"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        log_security_event("inactive_user_access", {"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    logger.debug(f"Authenticated user: {user.id}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure current user is active.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
    """
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure current user is an admin.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """
    Extract client information from request.
    
    Args:
        request: FastAPI request
        
    Returns:
        Tuple of (user_agent, ip_address)
    """
    user_agent = request.headers.get("user-agent")
    
    # Try to get real IP from proxy headers
    ip_address = (
        request.headers.get("x-forwarded-for") or
        request.headers.get("x-real-ip") or
        request.client.host if request.client else None
    )
    
    return user_agent, ip_address
