"""Device registration and connection management routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.lifecycle import ServiceContainer
from app.core.responses import success_response

from .dependencies import get_service_container

router = APIRouter(prefix="/devices", tags=["devices"])


class ConnectDeviceRequest(BaseModel):
    """Request body for connecting a device."""

    device_id: str = Field(..., min_length=1, max_length=128)
    protocol: str = Field(..., min_length=1, max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/connect", status_code=status.HTTP_201_CREATED)
async def connect_device(
    payload: ConnectDeviceRequest,
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """Register a device connection in the pool.

    Args:
        payload: Device connection request body.
        container: Application service container.

    Returns:
        Normalized API response with the created connection handle.
    """
    handle = await container.connection_pool.acquire(
        device_id=payload.device_id,
        protocol=payload.protocol,
        metadata=payload.metadata,
    )
    return success_response(
        {
            "device_id": handle.device_id,
            "protocol": handle.protocol,
            "connected_at": handle.connected_at.isoformat(),
            "last_heartbeat_at": handle.last_heartbeat_at.isoformat(),
            "metadata": dict(handle.metadata),
        },
        message="device connected",
    )


@router.delete("/{device_id}")
async def disconnect_device(
    device_id: str,
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """Disconnect a device from the pool.

    Args:
        device_id: Unique device identifier.
        container: Application service container.

    Returns:
        Normalized API response.
    """
    await container.connection_pool.release(device_id)
    return success_response({"device_id": device_id}, message="device disconnected")


@router.get("")
async def list_devices(
    container: Annotated[ServiceContainer, Depends(get_service_container)],
) -> dict[str, object]:
    """List active device connections.

    Args:
        container: Application service container.

    Returns:
        Normalized API response containing the pool snapshot.
    """
    return success_response(await container.connection_pool.snapshot(), message="active device snapshot")

