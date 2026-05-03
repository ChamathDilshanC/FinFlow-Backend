"""
Alembic migration environment.

Uses the synchronous ``psycopg2`` URL derived from ``DATABASE_URL`` so migrations
run without requiring an async engine. Imports ORM models so ``target_metadata``
is fully populated for autogenerate workflows.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

from app.config import get_settings
from app.infrastructure.database.base import Base
import app.infrastructure.database.models  # noqa: F401 — register ORM mappers on ``Base.metadata``

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    """Return sync DB URL for offline/online Alembic operations."""
    return get_settings().database_url_sync


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL only)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic against a live connection."""
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (execute DDL against the database)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
