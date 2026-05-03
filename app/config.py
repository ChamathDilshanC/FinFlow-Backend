"""
Application configuration loaded from environment variables.

Uses ``pydantic-settings`` for validation and documentation of runtime settings.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the API process.

    Attributes:
        app_name: Human-readable service name (logging, OpenAPI).
        debug: When True, enables verbose behavior where applicable.
        database_url: Async SQLAlchemy URL (``postgresql+asyncpg://...``).
        database_use_pooler: When True, applies asyncpg options compatible with
            PgBouncer transaction pooling (e.g. Supabase pooler on port 6543).
        supabase_url: HTTPS origin for JWKS and JWT issuer (no trailing path).
        supabase_jwt_legacy_hs256_secret: Optional legacy symmetric secret for HS256 tokens.
        supabase_jwt_issuer: Override JWT ``iss`` validation (default ``{supabase_url}/auth/v1``).
        supabase_jwt_audience: JWT ``aud`` claim (default ``authenticated``).
        refresh_token_expire_days: Reserved for future refresh-token flow.
        log_level: Root logging level.
        log_format: ``json`` for structured logs; ``text`` for console-friendly lines.
        cors_origins: Allowed browser origins for CORS preflight and responses.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Subscription Finance Tracker"
    debug: bool = False

    database_url: PostgresDsn = Field(
        ...,
        description="Must use asyncpg driver, e.g. postgresql+asyncpg://user:pass@host:5432/db",
    )
    database_use_pooler: bool = False

    supabase_url: str = Field(
        ...,
        description="Project URL, e.g. https://YOUR_PROJECT.supabase.co",
    )
    supabase_jwt_legacy_hs256_secret: str | None = Field(
        default=None,
        description="Legacy JWT Secret (HS256). Used only if ES256/JWKS verification fails.",
    )
    supabase_jwt_issuer: str | None = Field(
        default=None,
        description="Expected JWT iss claim; defaults to {SUPABASE_URL}/auth/v1",
    )
    supabase_jwt_audience: str = Field(
        default="authenticated",
        description="Expected JWT aud claim for Supabase user access tokens",
    )
    refresh_token_expire_days: int = 7  # Reserved for refresh-token support

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url", mode="before")
    @classmethod
    def ensure_async_driver(cls, v: str) -> str:
        """Require the asyncpg dialect for runtime database connections."""
        if not str(v).startswith("postgresql+asyncpg://"):
            msg = "DATABASE_URL must use postgresql+asyncpg:// for the async engine"
            raise ValueError(msg)
        return v

    def cors_origin_list(self) -> list[str]:
        """Return parsed CORS origins as a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("supabase_url", mode="before")
    @classmethod
    def normalize_supabase_url(cls, v: str) -> str:
        """Require HTTPS and strip trailing slashes from the Supabase project URL."""
        s = str(v).strip().rstrip("/")
        if not s.lower().startswith("https://"):
            msg = "SUPABASE_URL must use https://"
            raise ValueError(msg)
        return s

    @property
    def database_url_sync(self) -> str:
        """
        Sync SQLAlchemy URL for Alembic offline/online migrations.

        Uses ``psycopg2`` which matches ``requirements.txt`` for ``alembic upgrade``.
        """
        url = str(self.database_url)
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings singleton suitable for FastAPI ``Depends``.

    Returns:
        Parsed :class:`Settings` instance.
    """
    return Settings()
