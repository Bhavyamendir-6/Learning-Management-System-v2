"""
database/connection.py — Async SQLAlchemy engine + session factory for Neon PostgreSQL.

Neon-specific optimizations applied:
  - pool_size=5 / max_overflow=10  (Neon free tier: max 10 concurrent connections)
  - pool_recycle=1800              (recycle before Neon's ~5-min idle timeout)
  - pool_pre_ping=True             (detect stale connections after serverless wake-up)
  - statement_timeout=30s          (prevent runaway queries)
  - idle_in_transaction_session_timeout=60s (avoid holding idle tx connections)

Usage:
    from ..database.connection import get_session, create_tables

    async with get_session() as db:
        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()

    # One-time schema bootstrap (idempotent):
    await create_tables()
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models import Base


# ─────────────────────────────────────────────────────────────────────────────
# Engine construction
# ─────────────────────────────────────────────────────────────────────────────


def _build_async_url(raw_url: str) -> str:
    """
    Ensure the PostgreSQL URL uses the asyncpg driver scheme.
    Accepts:  postgresql://...  postgres://...  postgresql+asyncpg://...
    Returns:  postgresql+asyncpg://...
    """
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    raise ValueError(
        f"Unsupported PostgreSQL URL scheme: {raw_url[:30]}... "
        "Expected postgresql://, postgres://, or postgresql+asyncpg://"
    )


def _create_engine() -> AsyncEngine:
    raw_url = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")
    if not raw_url:
        raise RuntimeError(
            "POSTGRES_URL environment variable is required for PostgreSQL connection. "
            "Set it to your Neon connection string."
        )
    url = _build_async_url(raw_url)

    return create_async_engine(
        url,
        # ── Connection pool (Neon serverless tuned) ──────────────────────────
        pool_size=5,  # base pool — keeps 5 warm connections
        max_overflow=10,  # burst up to 15 total when under load
        pool_timeout=30,  # seconds to wait for a connection before raising
        pool_recycle=1800,  # recycle connections after 30min (before Neon idle kill)
        pool_pre_ping=True,  # sends "SELECT 1" before using a pooled connection
        # ── asyncpg connect args ──────────────────────────────────────────────
        connect_args={
            "server_settings": {
                "application_name": "lms_agent_ui",
                # Kill queries running > 30s (prevents blocking worker threads)
                "statement_timeout": "30000",
                # Release idle-in-transaction connections after 60s
                "idle_in_transaction_session_timeout": "60000",
            }
        },
        echo=False,  # set True only for SQL debugging
    )


engine: AsyncEngine = _create_engine()


# ─────────────────────────────────────────────────────────────────────────────
# Session factory
# ─────────────────────────────────────────────────────────────────────────────

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # keep objects usable after commit
    autoflush=False,  # explicit flush control
    autocommit=False,
)


# ─────────────────────────────────────────────────────────────────────────────
# Context manager helper (auto-commit / rollback)
# ─────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that provides a database session.

    Automatically commits on clean exit, rolls back on exception.

    Example:
        async with get_session() as db:
            db.add(some_model_instance)
        # committed here
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Schema bootstrap (idempotent)
# ─────────────────────────────────────────────────────────────────────────────


async def create_tables() -> None:
    """
    Create all application tables that do not yet exist in the database.

    This is idempotent (CREATE TABLE IF NOT EXISTS semantics via SQLAlchemy's
    checkfirst=True on create_all).

    NOTE: For production schema migrations (column additions, renames, etc.)
    use Alembic. This function is suitable only for initial provisioning and
    development resets.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def drop_tables() -> None:
    """
    Drop all application tables.
    DANGER: irreversible data loss. Use only in test environments.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
