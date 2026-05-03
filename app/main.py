"""
ASGI entrypoint configuring middleware, routes, logging, and exception handling.

Public JSON routes live under ``/api/v1``. ``GET /health`` is unauthenticated for probes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Configure startup/shutdown hooks (logging today; pools/engine hooks later)."""
    configure_logging(get_settings())
    yield


def create_app() -> FastAPI:
    """
    Build the FastAPI application with CORS, routers, and error normalization.

    Returns:
        Configured :class:`FastAPI` instance.
    """
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix="/api/v1")

    @app.get("/health", tags=["ops"])
    async def health() -> dict[str, str]:
        """
        Liveness/readiness style probe for load balancers and orchestrators.

        Returns:
            Static ``status`` field for simple automation checks.
        """
        return {"status": "ok"}

    return app


app = create_app()
