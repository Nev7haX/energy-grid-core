"""Historical telemetry query routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.lifecycle import ServiceContainer
from app.core.responses import success_response

from .dependencies import get_service_container

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{device_id}")
async def get_device_history(
    device_id: str,
    container: Annotated[ServiceContainer, Depends(get_service_container)],
    metric_name: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=5000),
) -> dict[str, object]:
    """Query historical telemetry for one device.

    Args:
        device_id: Unique device identifier.
        container: Application service container.
        metric_name: Optional metric filter.
        limit: Maximum number of rows to return.

    Returns:
        Normalized API response with telemetry history rows.
    """
    await container.stream_processor.drain()
    rows = await container.monitoring_service.get_history(
        device_id,
        metric_name=metric_name,
        limit=limit,
    )
    return success_response(rows, message="device history", total=len(rows))
