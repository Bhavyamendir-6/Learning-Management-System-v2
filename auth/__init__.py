"""
auth/ — JWT authentication module for the LMS Agent.

Public API:
    from ..auth import register_user, authenticate_user, create_access_token
    from ..auth import require_auth   # Flask decorator
    from ..auth import UserCreate, UserLogin
"""

from .handler import (
    register_user,
    authenticate_user,
    create_access_token,
    decode_access_token,
)
from .models import UserCreate, UserLogin

__all__ = [
    "register_user",
    "authenticate_user",
    "create_access_token",
    "decode_access_token",
    "UserCreate",
    "UserLogin",
]
