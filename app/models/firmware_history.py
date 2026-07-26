"""FirmwareHistory model — tracks firmware version changes over time."""

from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class FirmwareHistory(Base):
    """Records each firmware version change detected on a device."""

    __tablename__ = "firmware_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_mac: Mapped[str] = mapped_column(String(17), nullable=False, index=True)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    old_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<FirmwareHistory({self.device_name} {self.old_version} → {self.new_version})>"
