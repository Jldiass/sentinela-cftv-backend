import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Camera, CameraStatusPeriod
from .presentation import stream_path

logger = logging.getLogger("cftv.camera_status")


def ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def record_statuses(db: Session, statuses: dict[str, str], now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    cameras = db.scalars(select(Camera).order_by(Camera.id)).all()
    changed = 0
    for camera in cameras:
        current_status = (
            statuses.get(stream_path(camera.stream_key), "offline")
            if camera.enabled
            else "offline"
        )
        open_period = db.scalar(
            select(CameraStatusPeriod)
            .where(
                CameraStatusPeriod.camera_id == camera.id,
                CameraStatusPeriod.ended_at.is_(None),
            )
            .order_by(CameraStatusPeriod.started_at.desc())
            .limit(1)
        )
        if open_period and open_period.status == current_status:
            continue
        if open_period:
            open_period.ended_at = now
        db.add(
            CameraStatusPeriod(
                camera_id=camera.id,
                status=current_status,
                started_at=now,
            )
        )
        changed += 1
    if changed:
        db.commit()
        logger.info("camera status transitions recorded count=%s", changed)
    return changed


def period_duration_seconds(period: CameraStatusPeriod, now: datetime | None = None):
    end = period.ended_at
    if end is None:
        return None
    return max(
        0, int((ensure_utc(end) - ensure_utc(period.started_at)).total_seconds())
    )
