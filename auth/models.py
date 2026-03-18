"""
auth/models.py — Pydantic models for user registration and login payloads,
plus the database record schema for stored users.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Request payload models (used for input validation)
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Payload for POST /api/auth/signup."""

    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 32:
            raise ValueError("Username must be at most 32 characters")
        if not v.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError("Username may only contain letters, digits, _, -, .")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strong_enough(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    """Payload for POST /api/auth/login."""

    username: str
    password: str

    @field_validator("username")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().lower()


# ---------------------------------------------------------------------------
# Database record schema (what gets stored in PostgreSQL)
# ---------------------------------------------------------------------------


class UserInDB(BaseModel):
    """Represents a user record as stored in the PostgreSQL `users` table."""

    # Primary key is stored as a UUID string
    id: Optional[str] = None  # database primary key as string
    username: str  # unique, lowercase
    email: str  # unique, lowercase
    hashed_password: str  # bcrypt hash
    created_at: datetime = datetime.utcnow()
    is_active: bool = True

    class Config:
        # Allow population from database dicts (where _id maps to primary key)
        populate_by_name = True
