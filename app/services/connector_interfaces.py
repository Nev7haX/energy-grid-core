"""Connector-facing interfaces and telemetry payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


@dataclass(slots=True)
class ConnectorRegistration:
    """Represents a device connection request.

    Attributes:
        device_id: Unique device identifier.
        protocol: Connector protocol name.
        metadata: Optional device metadata.
    """

    device_id: str
    protocol: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TelemetrySample:
    """Normalized telemetry sample emitted by any device connector.

    Attributes:
        device_id: Unique device identifier.
        metric_name: Metric name such as `power_kw`.
        metric_value: Numeric metric value.
        quality: Data quality indicator.
        occurred_at: UTC event time.
        attributes: Optional auxiliary dimensions.
    """

    device_id: str
    metric_name: str
    metric_value: float
    quality: str = "good"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: dict[str, Any] = field(default_factory=dict)


class ConnectorAdapter(Protocol):
    """Protocol to abstract concrete device communication drivers."""

    async def connect(self, registration: ConnectorRegistration) -> None:
        """Open the underlying connector session.

        Args:
            registration: Device registration metadata.

        Returns:
            None.
        """

    async def disconnect(self, device_id: str) -> None:
        """Close the connector session for the device.

        Args:
            device_id: Unique device identifier.

        Returns:
            None.
        """

    async def read(self, device_id: str) -> TelemetrySample:
        """Read one telemetry sample from the connector.

        Args:
            device_id: Unique device identifier.

        Returns:
            Normalized telemetry sample.
        """

