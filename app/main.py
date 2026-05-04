"""
ASGI entrypoint configuring middleware, routes, logging, and exception handling.

Public JSON routes live under ``/api/v1``. ``GET /health`` is unauthenticated for probes.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging_config import configure_logging

API_V1_AREAS: list[dict[str, str]] = [
    {"path": "/api/v1/auth", "summary": "Email/password register & login (Supabase); profile /me"},
    {"path": "/api/v1/subscriptions", "summary": "Subscriptions CRUD"},
    {"path": "/api/v1/dashboard", "summary": "Dashboard aggregates"},
    {"path": "/api/v1/categories", "summary": "Categories"},
    {"path": "/api/v1/transactions", "summary": "Transactions"},
    {"path": "/api/v1/payments", "summary": "Payments"},
    {"path": "/api/v1/notifications", "summary": "Notification preferences"},
    {"path": "/api/v1/budgets", "summary": "Budget allocations"},
    {"path": "/api/v1/exchange-rates", "summary": "Exchange rates"},
]


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

    @app.get("/", tags=["ops"])
    async def root() -> dict[str, Any]:
        """Service index: API areas, auth flow, and doc links (no secrets)."""
        return {
            "service": settings.app_name,
            "status": "running",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json",
            },
            "authentication": {
                "scheme": "HTTP Bearer",
                "description": (
                    "Supabase Auth user access_token (JWT). Obtain via Supabase client "
                    "(email, Google, etc.) or this API's register/login when configured."
                ),
                "header": "Authorization: Bearer <access_token>",
                "jwt_verification": "ES256 via Supabase JWKS (SUPABASE_URL); optional HS256 legacy secret.",
                "public_endpoints_no_bearer": [
                    "GET /",
                    "GET /health",
                    "GET /docs",
                    "GET /redoc",
                    "GET /openapi.json",
                    "POST /api/v1/auth/register",
                    "POST /api/v1/auth/login",
                ],
                "register_login_note": (
                    "POST /api/v1/auth/register and /login call Supabase from the server; "
                    "requires SUPABASE_ANON_KEY on the host. Returns session tokens."
                ),
                "protected_typical": (
                    "Most other /api/v1/* routes require a valid Bearer token; "
                    "example: GET /api/v1/auth/me"
                ),
            },
            "api_version": "v1",
            "api_base_path": "/api/v1",
            "endpoints_by_area": API_V1_AREAS,
        }

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
