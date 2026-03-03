"""Centralized exception definitions and handlers."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class BaseAppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, status_code: int = 500, detail: str = "Internal server error") -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class DatabaseException(BaseAppException):
    """Raised on database-related failures."""

    def __init__(self, detail: str = "Database error") -> None:
        super().__init__(status_code=500, detail=detail)


class ExternalServiceException(BaseAppException):
    """Raised when an external service call fails (LLM, email, etc.)."""

    def __init__(self, detail: str = "External service error") -> None:
        super().__init__(status_code=502, detail=detail)


class NotFoundException(BaseAppException):
    """Raised when a requested resource is not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=404, detail=detail)


def _build_error_body(status_code: int, detail: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": {"code": status_code, "message": detail}}
    body["error"].update(extra)
    return body


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(BaseAppException)
    async def app_exception_handler(_request: Request, exc: BaseAppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_build_error_body(exc.status_code, exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        import logging

        logging.getLogger(__name__).exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content=_build_error_body(500, "Internal server error"),
        )
