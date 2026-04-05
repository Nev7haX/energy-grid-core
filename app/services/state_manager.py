"""Latest device state aggregation logic."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .connector_interfaces import TelemetrySample


@dataclass(slots=True)
class DeviceLatestState:
    """Aggregated latest state for one device.

    Attributes:
        device_id: Unique device identifier.
        last_seen_at: UTC timestamp of the latest telemetry event.
        health_state: Derived device health state.
        latest_metrics: Latest metric values by name.
        quality: Latest quality indicator.
    """

    device_id: str
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    health_state: str = "unknown"
    latest_metrics: dict[str, float] = field(default_factory=dict)
    quality: str = "unknown"


class DeviceStateManager:
    """Maintain device latest state optimized for monitoring reads."""

    def __init__(self) -> None:
        """Initialize the device state manager.

        Args:
            None.

        Returns:
            None.
        """
        self._states: dict[str, DeviceLatestState] = {}
        self._lock = asyncio.Lock()

    async def update_from_records(self, records: list[TelemetrySample]) -> None:
        """Update latest device state from flushed telemetry.

        Args:
            records: Telemetry batch emitted by the stream processor.

        Returns:
            None.
        """
        async with self._lock:
            for record in records:
                state = self._states.get(record.device_id)
                if state is None:
                    state = DeviceLatestState(device_id=record.device_id)
                    self._states[record.device_id] = state

                state.last_seen_at = record.occurred_at
                state.latest_metrics[record.metric_name] = record.metric_value
                state.quality = record.quality
                state.health_state = "healthy" if record.quality == "good" else "degraded"

    async def get_state(self, device_id: str) -> DeviceLatestState | None:
        """Return the latest device state if available.

        Args:
            device_id: Unique device identifier.

        Returns:
            Current device state or None.
        """
        async with self._lock:
            return self._states.get(device_id)

    async def list_states(self) -> list[DeviceLatestState]:
        """Return all tracked latest states.

        Args:
            None.

        Returns:
            List of current device states.
        """
        async with self._lock:
            return list(self._states.values())

