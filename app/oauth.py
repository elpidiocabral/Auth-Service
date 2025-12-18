"""OAuth authentication handlers for Facebook and other providers."""
import httpx
from typing import Optional, Dict
from app.config import FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET, FACEBOOK_REDIRECT_URI


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


facebook_oauth = FacebookOAuth()
