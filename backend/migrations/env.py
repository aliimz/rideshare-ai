"""
Alembic environment configuration with async SQLAlchemy support.

This module is invoked by Alembic for every migration command.  It:
  - Loads the DATABASE_URL from the environment (falling back to the default).
  - Imports all ORM models so their metadata is available for autogenerate.
  - Provides both online (async) and offline migration paths.

Running migrations:
    alembic -c backend/alembic.ini upgrade head
    alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Import all models so Alembic autogenerate can detect schema changes.
# ---------------------------------------------------------------------------
# noqa: F401 — imports required for side-effects (registering metadata)
import backend.db.models  # noqa: F401
from backend.db.database import Base

# ---------------------------------------------------------------------------
# Alembic Config object — provides access to values in alembic.ini.
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url with the runtime environment variable so that
# the value in alembic.ini is never used directly in production.
_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/rideshare",
)
config.set_main_option("sqlalchemy.url", _db_url)

# ---------------------------------------------------------------------------
# Logging — use alembic.ini's [loggers] section if it is present.
# ---------------------------------------------------------------------------
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Target metadata — enables autogenerate comparisons against the live DB.
# ---------------------------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline mode — emit SQL to stdout/file without a live DB connection.
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL statements without actually connecting to the database.
    Useful for producing SQL scripts that can be reviewed or applied manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode — connect to the database and apply migrations.
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic context with a live connection and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations inside an async context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # No connection pooling for migration runs
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode — bridges sync Alembic into async."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
