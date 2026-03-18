"""
auth/fastapi_middleware.py — FastAPI dependency for JWT authentication.

Usage:
    from fastapi import Depends
    from ..auth.fastapi_middleware import get_current_user

    @app.get("/api/protected")
    async def my_view(user: dict = Depends(get_current_user)):
        user_id = user["user_id"]
        username = user["username"]
        ...
"""

from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.handler import decode_access_token, AuthError

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """
    FastAPI dependency that enforces JWT authentication.
    Returns:
        {"user_id": "<uuid>", "username": "alice"}
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    return {"user_id": payload["sub"], "username": payload["username"]}
