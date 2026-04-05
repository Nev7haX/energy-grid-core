"""Response helpers for the API layer."""

from __future__ import annotations

from typing import Any


def success_response(
    data: Any = None,
    *,
    message: str = "ok",
    code: int = 200,
    total: int | None = None,
) -> dict[str, Any]:
    """Build a normalized success response body.

    Args:
        data: Response payload.
        message: Human-readable status message.
        code: Application-level status code.
        total: Optional total row count for list endpoints.

    Returns:
        Serialized response dictionary.
    """
    body: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        body["data"] = data
    if total is not None:
        body["total"] = total
    return body


def error_response(message: str, *, code: int, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a normalized error response body.

    Args:
        message: Human-readable error message.
        code: Application-level status code.
        details: Optional structured error details.

    Returns:
        Serialized error dictionary.
    """
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return payload

