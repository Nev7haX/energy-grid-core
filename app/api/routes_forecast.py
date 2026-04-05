"""Forecast invocation routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.core.lifecycle import ServiceContainer
from app.core.responses import success_response

from .dependencies import get_service_container

router = APIRouter(prefix="/forecast", tags=["forecast"])


@router.post("/{device_id}")
async def forecast_device_metric(
    device_id: str,
    container: Annotated[ServiceContainer, Depends(get_service_container)],
    metric_name: str = Query(..., min_length=1),
    horizon: int | None = Query(default=None, ge=1, le=1000),
) -> dict[str, object]:
    """Forecast one device metric through the configured provider interface.

    Args:
        device_id: Unique device identifier.
        container: Application service container.
        metric_name: Metric name to forecast.
        horizon: Number of future points to request.

    Returns:
        Normalized API response with forecast results.
    """
    resolved_horizon = horizon or get_settings().default_forecast_horizon
    await container.stream_processor.drain()
    payload = await container.monitoring_service.forecast_device(
        device_id=device_id,
        metric_name=metric_name,
        horizon=resolved_horizon,
    )
    return success_response(payload, message="forecast generated")
