"""Monitoring and telemetry ingestion routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.lifecycle import ServiceContainer
from app.core.responses import success_response
from app.services.connector_interfaces import TelemetrySample

from .dependencies import get_service_container

router = APIRouter(tags=["monitoring"])


class TelemetryIngestRequest(BaseModel):
    """Request body for ingesting one telemetry record."""

    device_id: str = Field(..., min_length=1, max_length=128)
    metric_name: str = Field(..., min_length=1, max_length=64)
    metric_value: float
    quality: str = Field(default="good", min_length=1, max_length=32)
    occurred_at: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


@router.post("/monitoring/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_telemetry(
    payload: TelemetryIngestRequest,
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """Submit one telemetry sample into the realtime processor.

    Args:
        payload: Telemetry request body.
        container: Application service container.

    Returns:
        Normalized API response with queue acceptance metadata.
    """
    await container.stream_processor.submit(
        TelemetrySample(
            device_id=payload.device_id,
            metric_name=payload.metric_name,
            metric_value=payload.metric_value,
            quality=payload.quality,
            occurred_at=payload.occurred_at or datetime.now(timezone.utc),
            attributes=payload.attributes,
        )
    )
    await container.connection_pool.heartbeat(payload.device_id)
    return success_response(
        {
            "device_id": payload.device_id,
            "metric_name": payload.metric_name,
        },
        message="telemetry accepted",
    )


@router.get("/monitoring/overview")
async def get_monitoring_overview(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """Return the current monitoring overview.

    Args:
        container: Application service container.

    Returns:
        Normalized API response with aggregated device state.
    """
    await container.stream_processor.drain()
    return success_response(await container.monitoring_service.build_overview(), message="monitoring overview")


@router.get("/system/health")
async def get_system_health(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """Return a lightweight health summary.

    Args:
        container: Application service container.

    Returns:
        Normalized API response with runtime health data.
    """
    snapshot = await container.connection_pool.snapshot()
    return success_response(
        {
            "status": "up",
            "active_connections": snapshot["active_connections"],
            "max_connections": snapshot["max_connections"],
            "queue_backpressure_enabled": True,
        },
        message="health ok",
    )
