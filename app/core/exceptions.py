"""
HTTP-aware exceptions producing the unified API error envelope.
"""

from fastapi import HTTPException


class AppHTTPException(HTTPException):
    """
    HTTP exception whose ``detail`` is always ``{"detail": str, "code": str}``.

    Args:
        detail: Human-readable message for API clients.
        code: Stable machine-readable error identifier.
        status_code: HTTP status to return.
    """

    def __init__(self, *, detail: str, code: str, status_code: int = 400) -> None:
        super().__init__(status_code=status_code, detail={"detail": detail, "code": code})
