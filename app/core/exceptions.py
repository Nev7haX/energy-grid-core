"""Application exception hierarchy and FastAPI registration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .responses import error_response


@dataclass(slots=True)
class ApplicationError(Exception):
    """Base application exception with HTTP and business codes.

    Attributes:
        message: Human-readable error message.
        status_code: HTTP status code.
        code: Application-level error code.
        details: Optional structured error details.
    """

    message: str
    status_code: int = 400
    code: int = 4000
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the base Exception message payload.

        Returns:
            None.
        """
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Raised when request or domain validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize validation error state.

        Args:
            message: Error message.
            details: Structured validation details.

        Returns:
            None.
        """
        super().__init__(
            message=message,
            status_code=422,
            code=4220,
            details=details or {},
        )


class NotFoundError(ApplicationError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize not-found error state.

        Args:
            message: Error message.
            details: Structured error details.

        Returns:
            None.
        """
        super().__init__(
            message=message,
            status_code=404,
            code=4040,
            details=details or {},
        )


class ConflictError(ApplicationError):
    """Raised when a resource conflict is detected."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize conflict error state.

        Args:
            message: Error message.
            details: Structured error details.

        Returns:
            None.
        """
        super().__init__(
            message=message,
            status_code=409,
            code=4090,
            details=details or {},
        )


class BackpressureError(ApplicationError):
    """Raised when telemetry ingestion exceeds current buffering capacity."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize backpressure error state.

        Args:
            message: Error message.
            details: Structured error details.

        Returns:
            None.
        """
        super().__init__(
            message=message,
            status_code=429,
            code=4290,
            details=details or {},
        )


async def _handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
    """Serialize known application errors.

    Args:
        _: Incoming request object.
        exc: Raised application error.

    Returns:
        JSON error response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.message, code=exc.code, details=exc.details or None),
    )


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Serialize FastAPI validation errors in the unified format.

    Args:
        _: Incoming request object.
        exc: Validation exception raised by FastAPI.

    Returns:
        JSON error response.
    """
    return JSONResponse(
        status_code=422,
        content=error_response("Request validation failed.", code=4221, details={"errors": exc.errors()}),
    )


async def _handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    """Serialize unexpected errors without leaking internals.

    Args:
        _: Incoming request object.
        exc: Unexpected exception.

    Returns:
        JSON error response.
    """
    return JSONResponse(
        status_code=500,
        content=error_response(
            "Internal server error.",
            code=5000,
            details={"type": exc.__class__.__name__},
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app.

    Args:
        app: FastAPI application instance.

    Returns:
        None.
    """
    app.add_exception_handler(ApplicationError, _handle_application_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)

