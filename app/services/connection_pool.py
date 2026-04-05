"""Device connection pool primitives."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ConflictError, NotFoundError


@dataclass(slots=True)
class ConnectionHandle:
    """Connection metadata tracked by the pool.

    Attributes:
        device_id: Unique device identifier.
        protocol: Connector protocol name.
        connected_at: UTC time when the connection was registered.
        last_heartbeat_at: UTC time of the last pool heartbeat.
        metadata: Optional device metadata.
    """

    device_id: str
    protocol: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class DeviceConnectionPool:
    """Concurrency-safe connection registry for active devices."""

    def __init__(self, max_connections: int) -> None:
        """Initialize the device connection pool.

        Args:
            max_connections: Maximum number of active device sessions.

        Returns:
            None.
        """
        self._max_connections = max_connections
        self._connections: dict[str, ConnectionHandle] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, device_id: str, protocol: str, metadata: dict[str, Any] | None = None) -> ConnectionHandle:
        """Register a device connection in the pool.

        Args:
            device_id: Unique device identifier.
            protocol: Connector protocol name.
            metadata: Optional device metadata.

        Returns:
            Registered connection handle.

        Raises:
            ConflictError: If the device is already connected or the pool is full.
        """
        async with self._lock:
            if device_id in self._connections:
                raise ConflictError(f"Device '{device_id}' is already connected.")
            if len(self._connections) >= self._max_connections:
                raise ConflictError("Device connection pool is at capacity.")

            handle = ConnectionHandle(
                device_id=device_id,
                protocol=protocol,
                metadata=metadata or {},
            )
            self._connections[device_id] = handle
            return handle

    async def release(self, device_id: str) -> None:
        """Remove a device connection from the pool.

        Args:
            device_id: Unique device identifier.

        Returns:
            None.

        Raises:
            NotFoundError: If the device is not connected.
        """
        async with self._lock:
            if device_id not in self._connections:
                raise NotFoundError(f"Device '{device_id}' is not connected.")
            del self._connections[device_id]

    async def heartbeat(self, device_id: str) -> ConnectionHandle:
        """Refresh a device heartbeat timestamp.

        Args:
            device_id: Unique device identifier.

        Returns:
            Updated connection handle.

        Raises:
            NotFoundError: If the device is not connected.
        """
        async with self._lock:
            handle = self._connections.get(device_id)
            if handle is None:
                raise NotFoundError(f"Device '{device_id}' is not connected.")
            handle.last_heartbeat_at = datetime.now(timezone.utc)
            return handle

    async def is_connected(self, device_id: str) -> bool:
        """Return whether the device is currently connected.

        Args:
            device_id: Unique device identifier.

        Returns:
            True when connected.
        """
        async with self._lock:
            return device_id in self._connections

    async def snapshot(self) -> dict[str, Any]:
        """Return an immutable snapshot of pool state.

        Args:
            None.

        Returns:
            Snapshot dictionary describing active connections.
        """
        async with self._lock:
            devices = [
                {
                    "device_id": handle.device_id,
                    "protocol": handle.protocol,
                    "connected_at": handle.connected_at.isoformat(),
                    "last_heartbeat_at": handle.last_heartbeat_at.isoformat(),
                    "metadata": dict(handle.metadata),
                }
                for handle in self._connections.values()
            ]
            return {
                "active_connections": len(devices),
                "max_connections": self._max_connections,
                "devices": devices,
            }

