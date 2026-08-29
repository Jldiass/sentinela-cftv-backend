from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import HealthOut
from ..services.mediamtx import MediaMTXUnavailable, mediamtx

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
async def health(db: Session = Depends(get_db)):
    database_status = "up"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
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
        version="0.2.0",
        effective_retention_hours=settings.effective_retention_hours,
    )
