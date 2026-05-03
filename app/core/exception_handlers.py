"""
Register global exception handlers for consistent error responses.
"""

import jwt
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppHTTPException


def register_exception_handlers(app: FastAPI) -> None:
    """
    Attach handlers that normalize failures to ``{"detail","code"}``.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(AppHTTPException)
    async def app_http_exception_handler(
        _request: Request,
        exc: AppHTTPException,
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        # Keep envelope stable; include first issue only for concise client messaging.
        errs = exc.errors()
        first = errs[0] if errs else {}
        loc = ".".join(str(x) for x in first.get("loc", ()))
        msg = first.get("msg", "Invalid request")
        detail = f"{loc}: {msg}" if loc else str(msg)
        return JSONResponse(
            status_code=422,
            content={"detail": detail, "code": "VALIDATION_ERROR"},
        )

    @app.exception_handler(jwt.PyJWTError)
    async def jwt_error_handler(_request: Request, _exc: jwt.PyJWTError) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": "Could not validate credentials", "code": "INVALID_TOKEN"},
        )
