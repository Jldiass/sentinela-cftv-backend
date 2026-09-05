import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Event, PasswordResetToken, RefreshSession
from .routers import (
    administration,
    auth,
    camera_status,
    cameras,
    events,
    internal,
    mosaics,
    system,
)
from .services.camera_status import record_statuses
from .services.mediamtx import MediaMTXUnavailable, mediamtx
from .services.rbac import ensure_rbac_catalog
from .services.storage import storage

logger = logging.getLogger("cftv")


async def cleanup_expired_events():
    while True:
        cutoff = datetime.now(timezone.utc) - timedelta(
            hours=settings.effective_retention_hours
        )
        with SessionLocal() as db:
            result = db.execute(delete(Event).where(Event.clip_start < cutoff))
            db.execute(
                delete(PasswordResetToken).where(
                    PasswordResetToken.expires_at < datetime.now(timezone.utc)
                )
            )
            db.execute(
                delete(RefreshSession).where(
                    RefreshSession.expires_at < datetime.now(timezone.utc)
                )
            )
            db.commit()
            if result.rowcount:
                logger.info("removed expired event metadata count=%s", result.rowcount)
        await asyncio.sleep(60)


async def purge_expired_recordings():
    if not storage.is_configured:
        return
    while True:
        await asyncio.sleep(300)
        removed = await asyncio.to_thread(
            storage.purge_expired, settings.effective_retention_hours
        )
        if removed:
            logger.info("removed expired R2 recordings count=%s", removed)


async def monitor_camera_statuses():
    while True:
        try:
            statuses = await mediamtx.path_statuses()
        except MediaMTXUnavailable:
            statuses = {}
        with SessionLocal() as db:
            record_statuses(db, statuses)
        await asyncio.sleep(settings.status_poll_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_rbac_catalog(db)
    logger.info(
        "database ready; camera_limit=%s retention_hours=%s",
        settings.camera_limit,
        settings.effective_retention_hours,
    )
    cleanup_task = asyncio.create_task(cleanup_expired_events())
    status_task = asyncio.create_task(monitor_camera_statuses())
    purge_task = asyncio.create_task(purge_expired_recordings())
    if storage.is_configured:
        logger.info("R2 storage configured; recordings offloaded from local disk")
    try:
        yield
    finally:
        cleanup_task.cancel()
        status_task.cancel()
        purge_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task
        with suppress(asyncio.CancelledError):
            await status_task
        with suppress(asyncio.CancelledError):
            await purge_task


app = FastAPI(
    title="Malupe Cam API",
    description="Backend para ingestão, monitoramento, gravação e eventos CFTV.",
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(system.router)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(administration.router, prefix=settings.api_prefix)
app.include_router(cameras.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(mosaics.router, prefix=settings.api_prefix)
app.include_router(camera_status.router, prefix=settings.api_prefix)
app.include_router(internal.router)
app.mount("/assets", StaticFiles(directory="app/static"), name="assets")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith(settings.api_prefix):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
def demo_frontend():
    return FileResponse("app/static/index.html")
