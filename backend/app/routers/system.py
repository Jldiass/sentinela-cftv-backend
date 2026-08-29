from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import HealthOut
from ..services.mediamtx import MediaMTXUnavailable, mediamtx

router = APIRouter(tags=["system"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/health", response_model=HealthOut)
async def health(db: DbSession):
    database_status = "up"
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        database_status = "down"
    mediamtx_status = "up"
    try:
        paths = await mediamtx.path_statuses()
    except MediaMTXUnavailable:
        mediamtx_status = "down"
        paths = {}
    return HealthOut(
        ok=database_status == "up" and mediamtx_status == "up",
        database=database_status,
        mediamtx=mediamtx_status,
        active_streams=len(paths),
        version=settings.app_version,
        effective_retention_hours=settings.effective_retention_hours,
    )
