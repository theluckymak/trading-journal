"""
Authentication routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import UserCreate, UserLogin, UserResponse, TokenResponse, RefreshTokenRequest, UserUpdate
from app.services.auth_service import AuthService
from app.services.oauth_service import OAuthService
from app.middleware.auth import get_current_user, get_client_info
from app.models.user import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    auth_service = AuthService(db)
    user = auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login user and return access + refresh tokens.
    Refresh token is set as HttpOnly cookie.
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Get client info
    user_agent, ip_address = get_client_info(request)
    
    # Create tokens
    access_token, refresh_token = auth_service.create_tokens(
        user=user,
        user_agent=user_agent,
        ip_address=ip_address
    )
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=dict)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    auth_service = AuthService(db)
    
    new_access_token = auth_service.refresh_access_token(token_data.refresh_token)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    token_data: RefreshTokenRequest,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout user by revoking refresh token."""
    auth_service = AuthService(db)
    auth_service.revoke_refresh_token(token_data.refresh_token)
    
    # Clear cookie
    response.delete_cookie("refresh_token")
    
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout user from all devices by revoking all refresh tokens."""
    auth_service = AuthService(db)
    count = auth_service.revoke_all_user_tokens(current_user.id)
    
    # Clear cookie
    response.delete_cookie("refresh_token")
    
    return {"message": f"Logged out from {count} device(s)"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile."""
    auth_service = AuthService(db)
    
    # Update user fields
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    if user_data.email is not None and user_data.email != current_user.email:
        # Check if email is already taken
        existing_user = auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_data.email
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/oauth/{provider}/token", response_model=TokenResponse)
async def oauth_login(
    provider: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback and login.
    Expects JSON body with 'access_token' from OAuth provider.
    """
    print(f"\n=== OAuth Login Request ===")
    print(f"Provider: {provider}")
    
    if provider not in ['google', 'github']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth provider"
        )
    
    # Get access token from request body
    body = await request.json()
    access_token = body.get('access_token')
    
    print(f"Access token received: {access_token[:20] if access_token else 'None'}...")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access token required"
        )
    
    oauth_service = OAuthService(db)
    
    # Get user info from provider
    if provider == 'google':
        user_info = await oauth_service.get_google_user_info(access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get Google user info"
            )
        
        oauth_id = user_info.get('id')
        email = user_info.get('email')
        full_name = user_info.get('name')
        profile_image = user_info.get('picture')
        
    else:  # github
        user_info = await oauth_service.get_github_user_info(access_token)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get GitHub user info"
            )
        
        oauth_id = str(user_info.get('id'))
        email = user_info.get('email')
        full_name = user_info.get('name')
        profile_image = user_info.get('avatar_url')
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by OAuth provider"
        )
    
    # Find or create user
    user = oauth_service.find_or_create_oauth_user(
        provider=provider,
        oauth_id=oauth_id,
        email=email,
        full_name=full_name,
        profile_image_url=profile_image
    )
    
    # Create tokens
    tokens = oauth_service.create_tokens_for_user(user)
    
    # Set refresh token as HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens['refresh_token'],
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=30 * 24 * 60 * 60  # 30 days
    )
    
    return {
        "access_token": tokens['access_token'],
        "refresh_token": tokens['refresh_token'],
        "token_type": "bearer"
    }

