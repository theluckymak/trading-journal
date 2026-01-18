"""
OAuth authentication service for Google and GitHub.
"""
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
import httpx

from app.config import settings
from app.models.user import User, UserRole
from app.services.token_service import token_service


class OAuthService:
    """Service for OAuth authentication with Google and GitHub."""
    
    def __init__(self, db: Session):
        """Initialize OAuth service."""
        self.db = db
        self.oauth = OAuth()
        
        # Configure Google OAuth
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.oauth.register(
                name='google',
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
        
        # Configure GitHub OAuth
        if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
            self.oauth.register(
                name='github',
                client_id=settings.GITHUB_CLIENT_ID,
                client_secret=settings.GITHUB_CLIENT_SECRET,
                access_token_url='https://github.com/login/oauth/access_token',
                access_token_params=None,
                authorize_url='https://github.com/login/oauth/authorize',
                authorize_params=None,
                api_base_url='https://api.github.com/',
                client_kwargs={'scope': 'user:email'}
            )
    
    async def get_google_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from Google using access token.
        
        Args:
            token: Google access token
            
        Returns:
            User info dict with id, email, name, picture
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                print(f"Fetching Google user info with token: {token[:20]}...")
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {token}'}
                )
                print(f"Google API response status: {response.status_code}")
                response.raise_for_status()
                user_data = response.json()
                print(f"Google user data: {user_data}")
                return user_data
        except httpx.TimeoutException as e:
            print(f"Timeout fetching Google user info: {e}")
            return None
        except Exception as e:
            print(f"Error fetching Google user info: {e}")
            return None
    
    async def get_github_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user info from GitHub using access token.
        
        Args:
            token: GitHub access token
            
        Returns:
            User info dict with id, email, name, avatar_url
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get user profile
                user_response = await client.get(
                    'https://api.github.com/user',
                    headers={
                        'Authorization': f'Bearer {token}',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                )
                user_response.raise_for_status()
                user_data = user_response.json()
                
                # Get primary email if not public
                if not user_data.get('email'):
                    emails_response = await client.get(
                        'https://api.github.com/user/emails',
                        headers={
                            'Authorization': f'Bearer {token}',
                            'Accept': 'application/vnd.github.v3+json'
                        }
                    )
                    emails_response.raise_for_status()
                    emails = emails_response.json()
                    
                    # Find primary verified email
                    primary_email = next(
                        (e['email'] for e in emails if e['primary'] and e['verified']),
                        None
                    )
                    if primary_email:
                        user_data['email'] = primary_email
                
                return user_data
        except Exception as e:
            print(f"Error fetching GitHub user info: {e}")
            return None
    
    def find_or_create_oauth_user(
        self,
        provider: str,
        oauth_id: str,
        email: str,
        full_name: Optional[str] = None,
        profile_image_url: Optional[str] = None
    ) -> User:
        """
        Find existing OAuth user or create new one.
        
        Args:
            provider: OAuth provider ('google' or 'github')
            oauth_id: Provider's user ID
            email: User email
            full_name: User's full name
            profile_image_url: User's profile image URL
            
        Returns:
            User instance
        """
        # Check if user exists with this OAuth provider
        user = self.db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_id == oauth_id
        ).first()
        
        if user:
            # Update user info
            user.email = email
            if full_name:
                user.full_name = full_name
            if profile_image_url:
                user.profile_image_url = profile_image_url
            self.db.commit()
            self.db.refresh(user)
            return user
        
        # Check if user exists with this email (regular account)
        user = self.db.query(User).filter(User.email == email).first()
        
        if user:
            # Link OAuth to existing account
            user.oauth_provider = provider
            user.oauth_id = oauth_id
            user.is_verified = True  # OAuth emails are verified
            if not user.full_name and full_name:
                user.full_name = full_name
            if not user.profile_image_url and profile_image_url:
                user.profile_image_url = profile_image_url
            self.db.commit()
            self.db.refresh(user)
            return user
        
        # Create new user
        new_user = User(
            email=email,
            full_name=full_name,
            profile_image_url=profile_image_url,
            oauth_provider=provider,
            oauth_id=oauth_id,
            is_verified=True,  # OAuth emails are verified
            is_active=True,
            role=UserRole.USER,
            hashed_password=None  # No password for OAuth users
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user
    
    def create_tokens_for_user(self, user: User) -> Dict[str, str]:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User instance
            
        Returns:
            Dict with access_token and refresh_token
        """
        access_token = token_service.create_access_token({"sub": str(user.id)})
        refresh_token = token_service.create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
