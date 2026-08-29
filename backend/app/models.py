from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Camera(Base):
    __tablename__ = "cameras"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(160), default="")
    stream_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    audio_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    # Compatibilidade com bancos criados antes da retenção se tornar global.
    retention_days_legacy: Mapped[int] = mapped_column(
        "retention_days", Integer, default=1
    )
    pre_alarm_seconds: Mapped[int] = mapped_column(Integer, default=30)
    post_alarm_seconds: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="camera", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    kind: Mapped[str] = mapped_column(String(60), default="alarm")
    note: Mapped[str] = mapped_column(Text, default="")
    happened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    clip_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    clip_duration: Mapped[int] = mapped_column(Integer)
    camera: Mapped[Camera] = relationship(back_populates="events")
