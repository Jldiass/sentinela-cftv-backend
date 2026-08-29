from datetime import datetime

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CameraBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    location: str = Field(default="", max_length=160)
    audio_enabled: bool = True
    retention_days: Literal[7] = 7
    pre_alarm_seconds: int = Field(default=30, ge=0, le=300)
    post_alarm_seconds: int = Field(default=60, ge=1, le=600)


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    location: str | None = Field(default=None, max_length=160)
    audio_enabled: bool | None = None
    retention_days: Literal[7] | None = None
    pre_alarm_seconds: int | None = Field(default=None, ge=0, le=300)
    post_alarm_seconds: int | None = Field(default=None, ge=1, le=600)
    enabled: bool | None = None


class CameraOut(CameraBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stream_key: str
    enabled: bool
    created_at: datetime
    status: Literal["online", "offline", "unstable"] = "offline"
    rtmp_url: str = ""
    hls_url: str = ""


class StreamCredentials(BaseModel):
    camera_id: int
    stream_key: str
    rtmp_url: str
    hls_url: str


class RecordingOut(BaseModel):
    start: datetime
    duration: float
    url: str


class EventCreate(BaseModel):
    kind: str = Field(default="alarm", max_length=60)
    note: str = Field(default="", max_length=500)
    happened_at: datetime | None = None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    camera_id: int
    kind: str
    note: str
    happened_at: datetime
    clip_start: datetime
    clip_duration: int
    playback_url: str


class HealthOut(BaseModel):
    ok: bool
    database: Literal["up", "down"]
    mediamtx: Literal["up", "down"]
    active_streams: int
    version: str
