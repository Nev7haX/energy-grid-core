"""Device registry model."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Device(TimestampMixin, Base):
    """Persisted device registry entry."""

    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    protocol: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

