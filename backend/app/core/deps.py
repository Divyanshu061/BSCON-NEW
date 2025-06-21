from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.utils.database import get_db
from app.models import User
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Retrieves the current user from either the access_token cookie (preferred for browsers)
    or from the Authorization header (used in Postman/ThunderClient).
    """
    jwt_token = request.cookies.get(settings.COOKIE_NAME) or token

     # ⬇️ Debug lines — add these
    print("🔍 Incoming cookies:", request.cookies)
    print("🔐 JWT token used:", jwt_token)

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(jwt_token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token: no subject")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user