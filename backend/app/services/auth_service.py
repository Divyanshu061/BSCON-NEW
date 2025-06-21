import httpx
from urllib.parse import urlencode
from typing import Optional, Dict

from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from app import crud, models
from app.core.config import settings

# Google OAuth2 endpoints
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"


class AuthService:
    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Construct the Google OAuth2 authorization URL.
        """
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"

    @staticmethod
    def exchange_code_for_token(code: str) -> Dict:
        """
        Exchange authorization code for access token from Google.
        """
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        response = httpx.post(GOOGLE_TOKEN_ENDPOINT, data=data)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch token from Google."
            )
        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict:
        """
        Retrieve user profile information using Google access token.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        response = httpx.get(GOOGLE_USERINFO_ENDPOINT, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user info from Google."
            )
        return response.json()

    @staticmethod
    def create_or_get_user(db: Session, user_info: Dict) -> models.User:
        """
        Fetch an existing user by email or create a new one.
        """
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google."
            )

        user = crud.get_user_by_email(db, email)
        if user:
            # Optionally update user info here if needed
            return user

        return crud.create_user(
            db,
            email=email,
            name=user_info.get("name", ""),
            profile_picture=user_info.get("picture")
        )

    @staticmethod
    def create_jwt_token(user: models.User) -> str:
        """
        Generate a JWT token for the authenticated user.
        """
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
