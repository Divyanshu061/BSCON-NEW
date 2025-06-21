# File: backend/app/routers/auth.py

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config

from app.core.config import settings
from app.core.deps import get_db
from app.core.security import verify_jwt_token
from app import crud, schemas
from app.services.auth_service import AuthService

# No prefix here; unified in main.py
router = APIRouter(tags=["auth"])
logger = logging.getLogger(__name__)

# OAuth2 configuration via OpenID Connect discovery
_oauth_config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
})
oauth = OAuth(_oauth_config)
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@router.get("/login/google", summary="Redirect to Google's OAuth2 login page")
async def login_google(request: Request) -> RedirectResponse:
    try:
        redirect_uri = str(settings.GOOGLE_REDIRECT_URI)
        logger.info("[OAuth] Redirecting to Google login, redirect_uri=%s", redirect_uri)
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except OAuthError as err:
        logger.error("[OAuth] Authorization redirect failed: %s", err)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to initiate Google OAuth flow.",
        )

@router.get("/callback/google", summary="Handle Google OAuth2 callback")
async def google_callback(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    try:
        # Exchange code for tokens
        token = await oauth.google.authorize_access_token(request)
        logger.info("[OAuth] Access token received")

        # Fetch user info from Google's userinfo endpoint
        userinfo_resp = await oauth.google.get(
            "https://www.googleapis.com/oauth2/v3/userinfo", token=token
        )
        if userinfo_resp.status_code != 200:
            logger.error("[OAuth] Failed to fetch user info, status=%s", userinfo_resp.status_code)
            raise OAuthError(description="Failed to fetch user info")

        user_info = userinfo_resp.json()
        email = user_info.get("email")
        if not email:
            logger.error("[OAuth] Email not found in user info")
            raise OAuthError(description="Missing email in user info response")
        logger.info("[OAuth] Fetched user info, email=%s", email)

    except OAuthError as err:
        logger.exception("[OAuth] Failed during token or user info retrieval: %s", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed.",
        )

    # Upsert user in database
    try:
        db_user = crud.get_user_by_email(db, email)
        if not db_user:
            db_user = crud.create_user(
                db,
                email=email,
                name=user_info.get("name"),
                profile_picture=user_info.get("picture"),
            )
            logger.info("[DB] Created user %s", email)
        else:
            db_user = crud.update_user(
                db,
                db_user,
                name=user_info.get("name"),
                profile_picture=user_info.get("picture"),
            )
            logger.info("[DB] Updated user %s", email)
    except Exception as err:
        logger.exception("[DB] User upsert error: %s", err)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error processing user.",
        )

    # Issue JWT and set cookie
    jwt_token = AuthService.create_jwt_token(db_user)
    print("🧪 Issued JWT token:", jwt_token)  # 👈 Debug print
    redirect_to = settings.FRONTEND_URL or "/"
    resp = RedirectResponse(url=redirect_to)
    resp.set_cookie(
        key=settings.COOKIE_NAME,
        value=jwt_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    logger.info("[Auth] Set JWT cookie and redirect to frontend")
    return resp

@router.get("/me", response_model=schemas.UserOut, summary="Get current user")
async def me(request: Request, db: Session = Depends(get_db)) -> schemas.UserOut:
    token = request.cookies.get(settings.COOKIE_NAME)
    if not token:
        logger.warning("[Auth] No JWT cookie present")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        user_id = verify_jwt_token(token)
    except Exception as err:
        logger.warning("[Auth] JWT verification failed: %s", err)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = crud.get_user(db, user_id)
    if not user:
        logger.warning("[Auth] User not found: %s", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist")
    return user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Logout user")
def logout(response: Response) -> None:
    response.delete_cookie(key=settings.COOKIE_NAME, path="/")
    logger.info("[Auth] Cleared JWT cookie for logout")