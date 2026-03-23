"""auth/handler.py — Authentication logic: register, login, JWT create/decode."""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import jwt
from dotenv import load_dotenv

from .models import UserCreate, UserInDB
from .password_utils import hash_password, verify_password

logger = logging.getLogger(__name__)

# Ensure project root is on sys.path for absolute imports (Tools, database, etc.)
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

load_dotenv()

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


async def register_user(payload: UserCreate) -> dict:
    """
    Register a new user. Returns their user dict on success.

    Raises:
        AuthError: if username or email already exists
    """
    from Tools.db_handler import create_user
    username = payload.username.lower().strip()
    try:
        hashed = hash_password(payload.password)
        user = await create_user(
            username=username,
            email=payload.email.lower().strip(),
            hashed_password=hashed,
        )
        logger.info("[auth] registered user=%s", username)
        return user
    except ValueError as e:
        logger.warning("[auth] registration failed user=%s reason=%s", username, e)
        raise AuthError(str(e), status_code=409)


async def authenticate_user(username: str, password: str) -> dict:
    """
    Verify credentials and return the user dict on success.

    Raises:
        AuthError: if username not found or password is incorrect
    """
    from Tools.db_handler import get_user_by_username
    norm = username.lower().strip()
    user = await get_user_by_username(norm)
    if not user:
        logger.warning("[auth] login failed user=%s reason=user_not_found", norm)
        raise AuthError("Invalid username or password", status_code=401)
    if not verify_password(password, user["hashed_password"]):
        logger.warning("[auth] login failed user=%s reason=bad_credentials", norm)
        raise AuthError("Invalid username or password", status_code=401)
    logger.info("[auth] login success user=%s", norm)
    return user


def create_access_token(user_id: str, username: str) -> str:
    """
    Create a signed JWT for the given user.

    Returns:
        str: Encoded JWT token
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT. Returns the payload dict or None on failure.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
