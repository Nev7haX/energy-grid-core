"""Optional aggregated history model for long-term storage."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class HistoryRecord(TimestampMixin, Base):
    """Persisted aggregated history record for long-term queries."""

    __tablename__ = "history_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    bucket_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    min_value: Mapped[float] = mapped_column(Float, nullable=False)
    max_value: Mapped[float] = mapped_column(Float, nullable=False)
    avg_value: Mapped[float] = mapped_column(Float, nullable=False)

