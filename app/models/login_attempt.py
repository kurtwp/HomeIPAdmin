"""LoginAttempt model — tracks failed login attempts for security."""

from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class LoginAttempt(Base):
    """Records every login attempt (success and failure)."""

    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"<LoginAttempt({status} user={self.username!r})>"
