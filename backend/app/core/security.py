from datetime import datetime, timedelta
from typing import Union

from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)    
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config
ALGORITHM = settings.JWT_ALGORITHM  # ✅ Use configured algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# --- Password hashing ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT creation ---
def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

# --- JWT verification ---
def verify_jwt_token(token: str) -> int:
    """
    Decode the JWT token and extract the user ID ("sub").
    Raises 401 if the token is invalid or expired.
    """
    logger.debug(f"🔐 Verifying JWT token: {token}")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        logger.debug(f"🧾 Decoded JWT payload: {payload}")
        user_id = payload.get("sub")

        if user_id is None:
            logger.warning("❌ JWT missing 'sub' field")
            raise HTTPException(status_code=401, detail="Invalid token: missing subject (sub)")

        return int(user_id)

    except JWTError as e:
        logger.error(f"❌ JWT decode failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    except ValueError as ve:
        logger.error(f"❌ JWT sub could not be converted to int: {ve}")
        raise HTTPException(status_code=401, detail="Invalid subject type")
