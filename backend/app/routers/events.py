import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Camera, Event
from ..schemas import EventCreate, EventOut
from ..services.presentation import event_output

router = APIRouter(tags=["events"])
logger = logging.getLogger("cftv.events")


@router.post(
    "/cameras/{camera_id}/events",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
)
def create_event(camera_id: int, payload: EventCreate, db: Session = Depends(get_db)):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, "Câmera não encontrada")
    if not camera.enabled:
        raise HTTPException(409, "Câmera desabilitada não pode receber eventos")
    happened = payload.happened_at or datetime.now(timezone.utc)
    if happened.tzinfo is None:
        happened = happened.replace(tzinfo=timezone.utc)
    start = happened - timedelta(seconds=camera.pre_alarm_seconds)
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
    db.commit()
    db.refresh(event)
    logger.info("created event_id=%s camera_id=%s", event.id, camera.id)
    return event_output(event, camera)


@router.get("/events", response_model=list[EventOut])
def list_events(
    camera_id: int | None = Query(default=None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Event)
        .options(selectinload(Event.camera))
        .order_by(Event.happened_at.desc())
        .limit(limit)
    )
    if camera_id is not None:
        stmt = stmt.where(Event.camera_id == camera_id)
    rows = db.scalars(stmt).all()
    return [event_output(row, row.camera) for row in rows]


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.scalar(
        select(Event).options(selectinload(Event.camera)).where(Event.id == event_id)
    )
    if not event:
        raise HTTPException(404, "Evento não encontrado")
    return event_output(event, event.camera)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "Evento não encontrado")
    db.delete(event)
    db.commit()
    logger.info("deleted event_id=%s; recordings preserved", event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
