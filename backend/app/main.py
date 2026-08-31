import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete

from .config import settings
from .database import Base, SessionLocal, engine
from .models import Event, PasswordResetToken, RefreshSession
from .routers import auth, cameras, events, internal, system

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


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    logger.info(
        "database ready; camera_limit=%s retention_hours=%s",
        settings.camera_limit,
        settings.effective_retention_hours,
    )
    cleanup_task = asyncio.create_task(cleanup_expired_events())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


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
app.include_router(cameras.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(internal.router)
app.mount("/assets", StaticFiles(directory="app/static"), name="assets")


@app.get("/", include_in_schema=False)
def demo_frontend():
    return FileResponse("app/static/index.html")
