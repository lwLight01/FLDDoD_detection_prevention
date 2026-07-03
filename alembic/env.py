"""
alembic/env.py
---------------
Alembic environment configuration for the Adaptive FL DDoS Detection system.

Supports both offline (script generation) and online (live DB) migration modes.
Reads DATABASE_URL from environment to support Docker Compose deployments.

Ref: docs/Database.md § 4 (Migration Strategy)
"""

from __future__ import with_statement

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Add src/ to PYTHONPATH so models can be imported ──────────────────────────
PROJECT_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Import ORM base and models so Alembic can detect schema changes
# (Models implemented in Milestone 4)
try:
    from mitigation_engine.db.models import Base  # noqa: F401
    target_metadata = Base.metadata
except ImportError:
    # Models not yet implemented — autogenerate will produce empty migration
    target_metadata = None

# Alembic Config object (provides access to alembic.ini values)
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Override sqlalchemy.url from environment variable ─────────────────────────
database_url = os.getenv("DATABASE_URL")
if database_url:
    # asyncpg driver URLs need to be converted to psycopg2 for Alembic
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL script without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (apply directly to a live database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,       # Detect column type changes
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
