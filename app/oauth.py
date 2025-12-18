"""
OAuth2 Generic Provider Handler
Supports multiple OAuth2 providers with a unified interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
from app.config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET, FACEBOOK_REDIRECT_URI
)


class OAuthProvider(ABC):
    """Abstract base class for OAuth providers"""

    @abstractmethod
    async def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL for redirecting user"""
        pass

    @abstractmethod
    async def get_user_info(self, code: str) -> Dict[str, Any]:
        """Exchange code for user info"""
        pass


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth2 Provider Implementation"""

    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
    AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"

    def __init__(
        self,
        client_id: str = GOOGLE_CLIENT_ID,
        client_secret: str = GOOGLE_CLIENT_SECRET,
        redirect_uri: str = GOOGLE_REDIRECT_URI,
        scopes: list = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or [
            "openid",
            "email",
            "profile"
        ]

    async def get_authorization_url(self, state: str) -> str:
        """Generate Google authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTHORIZATION_BASE_URL}?{query_string}"

    async def get_user_info(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for user info"""
        async with httpx.AsyncClient() as client:
            # Step 1: Exchange code for access token
            token_data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }

            try:
                token_response = await client.post(self.TOKEN_URL, data=token_data)
                token_response.raise_for_status()
                tokens = token_response.json()
                access_token = tokens.get("access_token")

                if not access_token:
                    raise ValueError("No access token in response")

                # Step 2: Get user info using access token
                headers = {"Authorization": f"Bearer {access_token}"}
                user_response = await client.get(self.USERINFO_URL, headers=headers)
                user_response.raise_for_status()
                user_info = user_response.json()

                return {
                    "provider": "google",
                    "provider_user_id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "first_name": user_info.get("given_name"),
                    "last_name": user_info.get("family_name"),
                    "picture_url": user_info.get("picture"),
                    "verified_email": user_info.get("verified_email", False)
                }
            except httpx.HTTPError as e:
                raise ValueError(f"OAuth provider error: {str(e)}")


class FacebookOAuth:
    """Handle Facebook OAuth flow."""
    
    AUTHORIZATION_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    USER_INFO_URL = "https://graph.facebook.com/v18.0/me"
    
    def __init__(self):
        self.client_id = FACEBOOK_CLIENT_ID
        self.client_secret = FACEBOOK_CLIENT_SECRET
        self.redirect_uri = FACEBOOK_REDIRECT_URI
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate Facebook OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "email,public_profile",
            "response_type": "code",
        }
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.AUTHORIZATION_URL}?{query_string}"
    
    async def get_access_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token."""
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.TOKEN_URL, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information from Facebook."""
        params = {
            "fields": "id,name,email",
            "access_token": access_token,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.USER_INFO_URL, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError:
                return None


class OAuthManager:
    """Manager for different OAuth providers"""

    def __init__(self):
        self.providers: Dict[str, OAuthProvider] = {
            "google": GoogleOAuthProvider()
        }

    def register_provider(self, name: str, provider: OAuthProvider):
        """Register a new OAuth provider"""
        self.providers[name] = provider

    def get_provider(self, name: str) -> Optional[OAuthProvider]:
        """Get a registered OAuth provider"""
        return self.providers.get(name)

    async def get_authorization_url(self, provider_name: str, state: str) -> str:
        """Get authorization URL for a provider"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        return await provider.get_authorization_url(state)

    async def get_user_info(self, provider_name: str, code: str) -> Dict[str, Any]:
        """Get user info from a provider"""
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        return await provider.get_user_info(code)


# Global OAuth manager instance
oauth_manager = OAuthManager()

# Facebook OAuth instance for backward compatibility
facebook_oauth = FacebookOAuth()