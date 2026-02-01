"""
OAuth Authentication Service for TerraSim
Supports Google and GitHub OAuth 2.0 authentication
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from pathlib import Path

import requests
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


@dataclass
class OAuthConfig:
    """OAuth provider configuration"""
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str
    user_info_url: str
    scopes: list


class OAuthProvider:
    """Abstract OAuth provider"""
    
    def __init__(self, config: OAuthConfig):
        self.config = config
    
    def parse_user_info(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse provider user info response - override in subclass"""
        return {
            'provider': 'unknown',
            'provider_id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture_url': None,
            'verified': False
        }
    
    def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL"""
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(self.config.scopes),
            'state': state
        }
        return f"{self.config.auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.config.redirect_uri,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }
            
            response = requests.post(self.config.token_url, data=data, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with provider"
            )
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information using access token"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(self.config.user_info_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get user info: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to retrieve user information"
            )


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            auth_url='https://accounts.google.com/o/oauth2/v2/auth',
            token_url='https://oauth2.googleapis.com/token',
            user_info_url='https://www.googleapis.com/oauth2/v2/userinfo',
            scopes=['openid', 'email', 'profile']
        )
        super().__init__(config)
    
    def parse_user_info(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Google user info response"""
        return {
            'provider': 'google',
            'provider_id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture_url': user_info.get('picture'),
            'verified': user_info.get('verified_email', False)
        }


class GitHubOAuthProvider(OAuthProvider):
    """GitHub OAuth 2.0 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        config = OAuthConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            auth_url='https://github.com/login/oauth/authorize',
            token_url='https://github.com/login/oauth/access_token',
            user_info_url='https://api.github.com/user',
            scopes=['user:email']
        )
        super().__init__(config)
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange code for token (GitHub needs Accept header)"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.config.redirect_uri,
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret
            }
            headers = {'Accept': 'application/json'}
            
            response = requests.post(
                self.config.token_url,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to authenticate with GitHub"
            )
    
    def parse_user_info(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GitHub user info response"""
        return {
            'provider': 'github',
            'provider_id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture_url': user_info.get('avatar_url'),
            'verified': True  # GitHub verifies email by default
        }


class OAuthService:
    """Manage OAuth authentication"""
    
    STATE_FILE = Path(__file__).parent.parent.parent / '.oauth_state'
    STATE_EXPIRY = timedelta(minutes=10)
    
    def __init__(self):
        """Initialize OAuth service with configured providers"""
        self.providers: Dict[str, OAuthProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize OAuth providers from environment variables"""
        # Google OAuth
        google_client_id = os.getenv('OAUTH_GOOGLE_CLIENT_ID')
        google_client_secret = os.getenv('OAUTH_GOOGLE_CLIENT_SECRET')
        google_redirect_uri = os.getenv('OAUTH_GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback/google')
        
        if google_client_id and google_client_secret:
            self.providers['google'] = GoogleOAuthProvider(
                google_client_id,
                google_client_secret,
                google_redirect_uri
            )
            logger.info("Google OAuth provider configured")
        
        # GitHub OAuth
        github_client_id = os.getenv('OAUTH_GITHUB_CLIENT_ID')
        github_client_secret = os.getenv('OAUTH_GITHUB_CLIENT_SECRET')
        github_redirect_uri = os.getenv('OAUTH_GITHUB_REDIRECT_URI', 'http://localhost:8000/auth/callback/github')
        
        if github_client_id and github_client_secret:
            self.providers['github'] = GitHubOAuthProvider(
                github_client_id,
                github_client_secret,
                github_redirect_uri
            )
            logger.info("GitHub OAuth provider configured")
    
    def generate_state(self) -> str:
        """Generate secure state parameter"""
        state = secrets.token_urlsafe(32)
        state_data = {
            'state': state,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATE_FILE, 'a') as f:
                f.write(json.dumps(state_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
        
        return state
    
    def verify_state(self, state: str) -> bool:
        """Verify state parameter"""
        if not self.STATE_FILE.exists():
            return False
        
        try:
            with open(self.STATE_FILE, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    if data['state'] == state:
                        # Check expiry
                        saved_time = datetime.fromisoformat(data['timestamp'])
                        if datetime.now() - saved_time < self.STATE_EXPIRY:
                            return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify state: {e}")
            return False
    
    def get_authorization_url(self, provider: str) -> Tuple[str, str]:
        """Get authorization URL for provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not configured")
        
        state = self.generate_state()
        url = self.providers[provider].get_authorization_url(state)
        return url, state
    
    def authenticate(self, provider: str, code: str) -> Dict[str, Any]:
        """Authenticate user with provider"""
        if provider not in self.providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider} not supported"
            )
        
        oauth_provider = self.providers[provider]
        
        # Exchange code for token
        token_data = oauth_provider.exchange_code_for_token(code)
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to obtain access token"
            )
        
        # Get user info
        user_info = oauth_provider.get_user_info(access_token)
        
        # Parse user info based on provider
        parsed_user = oauth_provider.parse_user_info(user_info)
        
        logger.info(f"User authenticated via {provider}: {parsed_user.get('email')}")
        
        return {
            'provider': provider,
            'user': parsed_user,
            'access_token': access_token,
            'token_data': token_data
        }
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if provider is available"""
        return provider in self.providers
    
    def get_available_providers(self) -> list:
        """Get list of available providers"""
        return list(self.providers.keys())


# Global OAuth service instance
_oauth_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
    """Get or create OAuth service"""
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService()
    return _oauth_service
