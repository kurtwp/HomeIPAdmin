"""DeviceFirmware model — tracks firmware versions for network devices."""

from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class DeviceFirmware(Base):
    """Tracks firmware versions for network devices."""

    __tablename__ = "device_firmware"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_mac: Mapped[str] = mapped_column(String(17), nullable=False, unique=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    available_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    update_available: Mapped[bool] = mapped_column(Boolean, default=False)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    auto_update_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DeviceFirmware({self.device_name} v={self.current_version})>"
