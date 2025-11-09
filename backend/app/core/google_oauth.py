from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.core.config import settings
from typing import Optional, Dict


class GoogleOAuth:
    """Google OAuth helper class for authentication"""

    @staticmethod
    async def verify_google_token(token: str) -> Optional[Dict]:
        """
        Verify Google ID token and extract user information

        Args:
            token: Google ID token from frontend

        Returns:
            Dict with user info (email, name, picture) or None if invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Token is valid, extract user information
            user_data = {
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False),
                "google_id": idinfo.get("sub"),
            }

            return user_data

        except ValueError as e:
            # Invalid token
            print(f"Google token verification failed: {str(e)}")
            return None
        except Exception as e:
            # Other errors
            print(f"Error verifying Google token: {str(e)}")
            return None

    @staticmethod
    def get_authorization_url() -> str:
        """
        Generate Google OAuth authorization URL

        Returns:
            Google OAuth URL for frontend to redirect to
        """
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }

        # Build query string
        query_params = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_params}"


google_oauth = GoogleOAuth()
