"""
mitigation_engine/db/database.py
-----------------------------------
SQLAlchemy async engine and session factory.

Uses asyncpg driver for non-blocking PostgreSQL queries.
Session lifecycle managed via FastAPI dependency injection.

Usage:
    from mitigation_engine.db.database import get_db

    @app.get("/example")
    async def example(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(User))
        ...

Ref: docs/Database.md, docs/DevelopmentRoadmap.md — Milestone 4 (schema),
     Milestone 23 (FastAPI DI integration)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    pass

# Import settings lazily to avoid circular imports
_engine = None
_SessionLocal = None


def _get_engine():
    """Lazily initialise the async engine using the configured DATABASE_URL."""
    global _engine
    if _engine is None:
        from mitigation_engine.config import settings

        # Convert standard postgres URL to asyncpg driver format
        url = settings.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

        _engine = create_async_engine(
            url,
            echo=False,           # Set True for SQL debug logging
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,   # Verify connections before use (handles DB restarts)
        )
    return _engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (and lazily create) the shared session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Avoid lazy-load errors after commit
        )
    return _SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    Usage:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...

    The session is automatically committed on success and rolled back on error.
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_engine() -> None:
    """Dispose of the engine connection pool. Call during application shutdown."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
