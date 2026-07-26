"""NotificationPreference model — per-event notification channel toggles."""

from sqlalchemy import String, Boolean, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db import Base


class NotificationPreference(Base):
    """Controls which notification channels are active for each event type.

    One row per (event_type, channel) combination. If no row exists,
    the channel is enabled for that event (opt-out model).
    """

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # email, webhook, pushover, telegram
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("event_type", "channel", name="uq_event_channel"),
    )

    def __repr__(self) -> str:
        return f"<NotificationPreference({self.event_type} → {self.channel} = {self.enabled})>"
