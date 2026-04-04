"""
Database engine, session factory, declarative base, and FastAPI dependency.

Usage:
    Set the DATABASE_URL environment variable to override the default connection.
    The default connects to a local PostgreSQL instance using asyncpg.

    In FastAPI route handlers, inject the session via:
        async def my_route(db: AsyncSession = Depends(get_db)): ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings

# ---------------------------------------------------------------------------
# Connection URL
# Railway provides postgresql:// but asyncpg requires postgresql+asyncpg://
# ---------------------------------------------------------------------------

_raw_url = settings.DATABASE_URL
DATABASE_URL: str = (
    _raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if _raw_url.startswith("postgresql://")
    else _raw_url
)

# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------

engine = create_async_engine(
    DATABASE_URL,
    echo=False,           # Set True to log all SQL statements for debugging
    pool_pre_ping=True,   # Verify connections before reuse
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ---------------------------------------------------------------------------
# Declarative base — all ORM models inherit from this
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy ORM models."""


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session for the duration of a request.

    The session is automatically closed (and rolled back on error) when the
    request context exits.  Inject it in route handlers with::

        async def my_route(db: AsyncSession = Depends(get_db)): ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
