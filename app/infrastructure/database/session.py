"""
Async engine and session lifecycle.

**Supabase / PgBouncer (transaction pooler):** When ``DATABASE_USE_POOLER=true``,
asyncpg prepared-statement caching is disabled. Transaction-mode poolers multiplex
many clients on few server connections and cannot safely pin prepared statements
to a single backend session. Session-mode poolers behave like direct Postgres
connections; you may set ``DATABASE_USE_POOLER=false`` if you use session mode.
"""

from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings


def _asyncpg_url_and_ssl(url: str) -> tuple[str, bool | None]:
    """
    asyncpg does not accept libpq ``sslmode`` query params (Supabase adds these).

    Strips ``sslmode`` from the URL and returns an ``ssl`` flag for ``connect_args``.

    Returns:
        Tuple of (cleaned URL string, ssl setting: True/False/None for default).
    """
    parts = urlsplit(url)
    if not parts.query:
        return url, None

    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "sslmode"]
    ssl_vals = [v for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() == "sslmode"]
    sslmode = ssl_vals[-1].lower() if ssl_vals else None

    new_query = urlencode(pairs)
    cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    ssl: bool | None
    if sslmode in ("disable", "allow", "prefer"):
        ssl = False if sslmode == "disable" else None
    elif sslmode in ("require", "verify-ca", "verify-full"):
        ssl = True
    else:
        ssl = None

    return cleaned, ssl


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    """
    Build the async SQLAlchemy engine using ``postgresql+asyncpg``.

    Args:
        settings: Application settings including ``database_url``.

    Returns:
        Configured :class:`AsyncEngine` with pooling defaults suitable for API usage.
    """
    connect_args: dict[str, Any] = {}
    if settings.database_use_pooler:
        # Required for PgBouncer transaction pooling with asyncpg (e.g. Supabase :6543).
        connect_args["statement_cache_size"] = 0
        connect_args["prepared_statement_cache_size"] = 0

    db_url, ssl = _asyncpg_url_and_ssl(str(settings.database_url))
    if ssl is not None:
        connect_args["ssl"] = ssl

    return create_async_engine(
        db_url,
        echo=settings.debug,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create a session factory bound to the given engine.

    Uses ``expire_on_commit=False`` so detached instances remain usable after
    commit when explicitly needed by repositories.

    Args:
        engine: Async SQLAlchemy engine.

    Returns:
        Session factory for request-scoped database work.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Lazily construct and cache the global async engine.

    Returns:
        Singleton :class:`AsyncEngine`.
    """
    global _engine
    if _engine is None:
        _engine = create_engine_from_settings(get_settings())
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Lazily construct and cache the async session factory.

    Returns:
        Singleton ``async_sessionmaker`` for :class:`AsyncSession`.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a request-scoped database session.

    Commits on success; rolls back on exception.

    Yields:
        Open :class:`AsyncSession`.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
