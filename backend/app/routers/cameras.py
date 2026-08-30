import logging
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Camera
from ..schemas import (
    CameraCreate,
    CameraOut,
    CameraUpdate,
    RecordingOut,
    StreamCredentials,
)
from ..services.mediamtx import MediaMTXUnavailable, mediamtx
from ..services.presentation import (
    camera_output,
    recording_output,
    stream_credentials,
    stream_path,
)

router = APIRouter(prefix="/cameras", tags=["cameras"])
logger = logging.getLogger("cftv.cameras")
DbSession = Annotated[Session, Depends(get_db)]


def camera_or_404(camera_id: int, db: Session) -> Camera:
    camera = db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(404, "Câmera não encontrada")
    return camera


async def statuses_or_empty() -> dict[str, str]:
    try:
        return await mediamtx.path_statuses()
    except MediaMTXUnavailable:
        return {}


@router.get("", response_model=list[CameraOut])
async def list_cameras(db: DbSession, include_disabled: bool = Query(False)):
    stmt = select(Camera).order_by(Camera.id)
    if not include_disabled:
        stmt = stmt.where(Camera.enabled.is_(True))
    rows = db.scalars(stmt).all()
    stream_statuses = await statuses_or_empty()
    return [
        camera_output(row, stream_statuses.get(stream_path(row.stream_key), "offline"))
        for row in rows
    ]


@router.post("", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate, db: DbSession):
    total = db.scalar(select(func.count()).select_from(Camera)) or 0
    if total >= settings.camera_limit:
        raise HTTPException(409, f"Limite de {settings.camera_limit} câmeras atingido")
    camera = Camera(
        **payload.model_dump(), stream_key=f"cam-{secrets.token_urlsafe(18).lower()}"
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    logger.info("created camera_id=%s", camera.id)
    return camera_output(camera)


@router.get("/{camera_id}", response_model=CameraOut)
async def get_camera(camera_id: int, db: DbSession):
    camera = camera_or_404(camera_id, db)
    stream_statuses = await statuses_or_empty()
    return camera_output(
        camera, stream_statuses.get(stream_path(camera.stream_key), "offline")
    )


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera(camera_id: int, payload: CameraUpdate, db: DbSession):
    camera = camera_or_404(camera_id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(camera, key, value)
    db.commit()
    db.refresh(camera)
    stream_statuses = await statuses_or_empty()
    logger.info(
        "updated camera_id=%s fields=%s", camera.id, sorted(payload.model_fields_set)
    )
    return camera_output(
        camera, stream_statuses.get(stream_path(camera.stream_key), "offline")
    )


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(camera_id: int, db: DbSession):
    camera = camera_or_404(camera_id, db)
    stream_statuses = await statuses_or_empty()
    if stream_path(camera.stream_key) in stream_statuses:
        raise HTTPException(409, "Desconecte a câmera antes de excluir o cadastro")
    db.delete(camera)
    db.commit()
    logger.info("deleted camera_id=%s; recordings preserved", camera_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{camera_id}/stream", response_model=StreamCredentials)
def get_stream_credentials(camera_id: int, db: DbSession):
    return stream_credentials(camera_or_404(camera_id, db))


@router.post("/{camera_id}/stream-key/rotate", response_model=StreamCredentials)
async def rotate_stream_key(camera_id: int, db: DbSession):
    camera = camera_or_404(camera_id, db)
    try:
        stream_statuses = await mediamtx.path_statuses()
    except MediaMTXUnavailable as exc:
        raise HTTPException(
            503, "Não foi possível confirmar se o canal está offline"
        ) from exc
    if stream_path(camera.stream_key) in stream_statuses:
        raise HTTPException(409, "Desconecte a câmera antes de trocar a chave RTMP")
    camera.stream_key = f"cam-{secrets.token_urlsafe(18).lower()}"
    db.commit()
    db.refresh(camera)
    logger.info("rotated stream key camera_id=%s", camera.id)
    return stream_credentials(camera)


@router.get("/{camera_id}/recordings", response_model=list[RecordingOut])
async def list_recordings(
    camera_id: int,
    db: DbSession,
    start: datetime | None = None,
    end: datetime | None = None,
):
    camera = camera_or_404(camera_id, db)
    if start and end and start >= end:
        raise HTTPException(422, "start deve ser anterior a end")
    try:
        rows = await mediamtx.list_recordings(
            stream_path(camera.stream_key), start, end
        )
    except MediaMTXUnavailable as exc:
        raise HTTPException(503, "Playback temporariamente indisponível") from exc
    return [recording_output(camera, row) for row in rows]
