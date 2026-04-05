"""Reusable API dependency providers."""

from __future__ import annotations

from fastapi import Request

from app.core.lifecycle import ServiceContainer


def get_service_container(request: Request) -> ServiceContainer:
    """Return the application service container from request state.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Application service container.
    """
    return request.app.state.container

