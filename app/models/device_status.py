"""Device latest status model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class DeviceStatus(TimestampMixin, Base):
    """Persisted latest state snapshot for a device."""

    __tablename__ = "device_statuses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), ForeignKey("devices.device_id"), index=True)
    connectivity_state: Mapped[str] = mapped_column(String(32), nullable=False)
    health_state: Mapped[str] = mapped_column(String(32), nullable=False)
    quality: Mapped[str] = mapped_column(String(32), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latest_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

