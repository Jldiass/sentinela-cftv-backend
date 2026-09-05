import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import settings
from ..database import get_db
from ..models import Camera, Event, User
from ..schemas import EventCreate, EventOut
from ..services.presentation import event_output
from ..services.rbac import accessible_camera_ids, audit
from .auth import require_permission

router = APIRouter(tags=["events"])
logger = logging.getLogger("cftv.events")
DbSession = Annotated[Session, Depends(get_db)]
EventReader = Annotated[User, Depends(require_permission("events.read"))]
EventManager = Annotated[User, Depends(require_permission("events.manage"))]


@router.post(
    "/cameras/{camera_id}/events",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    camera_id: int, payload: EventCreate, db: DbSession, user: EventManager
):
    camera = db.get(Camera, camera_id)
    allowed = accessible_camera_ids(db, user)
    if not camera or (allowed is not None and camera.id not in allowed):
        raise HTTPException(404, "Câmera não encontrada")
    if not camera.enabled:
        raise HTTPException(409, "Câmera desabilitada não pode receber eventos")
    happened = payload.happened_at or datetime.now(timezone.utc)
    if happened.tzinfo is None:
        happened = happened.replace(tzinfo=timezone.utc)
    happened = happened.astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    if happened > now + timedelta(minutes=1):
        raise HTTPException(422, "happened_at não pode estar no futuro")
    start = happened - timedelta(seconds=camera.pre_alarm_seconds)
    retention_cutoff = now - timedelta(hours=settings.effective_retention_hours)
    if start < retention_cutoff:
        raise HTTPException(422, "Evento fora da janela de retenção")
    duration = camera.pre_alarm_seconds + camera.post_alarm_seconds
    event = Event(
        camera_id=camera.id,
        kind=payload.kind,
        note=payload.note,
        happened_at=happened,
        clip_start=start,
        clip_duration=duration,
    )
    db.add(event)
    db.flush()
    audit(db, user, "event.create", "event", event.id, {"camera_id": camera.id})
    db.commit()
    db.refresh(event)
    logger.info("created event_id=%s camera_id=%s", event.id, camera.id)
    return event_output(event, camera)


@router.get("/events", response_model=list[EventOut])
def list_events(
    db: DbSession,
    user: EventReader,
    camera_id: int | None = Query(default=None),
    limit: int = Query(100, ge=1, le=500),
):
    stmt = (
        select(Event)
        .options(selectinload(Event.camera))
        .order_by(Event.happened_at.desc())
        .limit(limit)
    )
    if camera_id is not None:
        stmt = stmt.where(Event.camera_id == camera_id)
    allowed = accessible_camera_ids(db, user)
    if allowed is not None:
        stmt = stmt.where(Event.camera_id.in_(allowed))
    rows = db.scalars(stmt).all()
    return [event_output(row, row.camera) for row in rows]


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: DbSession, user: EventReader):
    event = db.scalar(
        select(Event).options(selectinload(Event.camera)).where(Event.id == event_id)
    )
    allowed = accessible_camera_ids(db, user)
    if not event or (allowed is not None and event.camera_id not in allowed):
        raise HTTPException(404, "Evento não encontrado")
    return event_output(event, event.camera)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: DbSession, user: EventManager):
    event = db.get(Event, event_id)
    allowed = accessible_camera_ids(db, user)
    if not event or (allowed is not None and event.camera_id not in allowed):
        raise HTTPException(404, "Evento não encontrado")
    audit(db, user, "event.delete", "event", event.id, {"camera_id": event.camera_id})
    db.delete(event)
    db.commit()
    logger.info("deleted event_id=%s; recordings preserved", event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
