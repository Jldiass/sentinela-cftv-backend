import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import cameras, events, internal, system

logger = logging.getLogger("cftv")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    logger.info("database ready; camera_limit=%s", settings.camera_limit)
    yield


app = FastAPI(
    title="Sentinela CFTV API",
    description="Backend para ingestão, monitoramento, gravação e eventos CFTV.",
    version="0.2.0",
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
app.include_router(cameras.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(internal.router)
app.mount("/assets", StaticFiles(directory="app/static"), name="assets")


@app.get("/", include_in_schema=False)
def demo_frontend():
    return FileResponse("app/static/index.html")
