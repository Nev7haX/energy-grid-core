"""Raw telemetry event model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TelemetryEvent(Base):
    """Persisted raw telemetry row."""

    __tablename__ = "telemetry_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[str] = mapped_column(String(32), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

