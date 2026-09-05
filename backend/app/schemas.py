from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class CameraBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=100)
    location: str = Field(default="", max_length=160)
    audio_enabled: bool = True
    pre_alarm_seconds: int = Field(default=30, ge=0, le=300)
    post_alarm_seconds: int = Field(default=60, ge=1, le=600)


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=100)
    location: str | None = Field(default=None, max_length=160)
    audio_enabled: bool | None = None
    pre_alarm_seconds: int | None = Field(default=None, ge=0, le=300)
    post_alarm_seconds: int | None = Field(default=None, ge=1, le=600)
    enabled: bool | None = None


class CameraOut(CameraBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    enabled: bool
    created_at: datetime
    status: Literal["online", "offline", "unstable"] = "offline"
    hls_url: str = ""
    effective_retention_hours: int


class StreamCredentials(BaseModel):
    camera_id: int
    stream_key: str
    stream_path: str
    rtmp_server_url: str
    rtmp_url: str
    hls_url: str


class RecordingOut(BaseModel):
    start: datetime
    duration: float
    url: str


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
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
    playback_url: str | None
    clip_status: Literal["pending", "available", "expired"]
    available_until: datetime


class HealthOut(BaseModel):
    ok: bool
    database: Literal["up", "down"]
    mediamtx: Literal["up", "down"]
    active_streams: int
    version: str
    effective_retention_hours: int


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        return " ".join(value.split())


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class AuthOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class ForgotPasswordOut(BaseModel):
    message: str
    debug_reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=256)
    new_password: str = Field(min_length=12, max_length=128)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class MessageOut(BaseModel):
    message: str


class PermissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    description: str


class RoleBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=240)
    permission_codes: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=240)
    permission_codes: list[str] | None = None


class RoleOut(RoleBase):
    id: int
    is_system: bool
    user_count: int
    created_at: datetime


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    is_active: bool = True
    role_ids: list[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    is_active: bool | None = None
    role_ids: list[int] | None = None


class UserAdminOut(UserOut):
    updated_at: datetime


class MosaicCameraInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    camera_id: int = Field(gt=0)
    position: int = Field(ge=1, le=36)


class MosaicBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    capacity: int = Field(ge=1, le=36)
    active: bool = True
    cameras: list[MosaicCameraInput] = Field(default_factory=list)
    user_ids: list[int] = Field(default_factory=list)
    role_ids: list[int] = Field(default_factory=list)


class MosaicCreate(MosaicBase):
    pass


class MosaicUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=120)
    capacity: int | None = Field(default=None, ge=1, le=36)
    active: bool | None = None
    cameras: list[MosaicCameraInput] | None = None
    user_ids: list[int] | None = None
    role_ids: list[int] | None = None


class MosaicCameraOut(BaseModel):
    camera_id: int
    position: int
    camera: CameraOut


class MosaicOut(BaseModel):
    id: int
    name: str
    capacity: int
    columns: int
    rows: int
    active: bool
    camera_count: int
    user_count: int
    cameras: list[MosaicCameraOut]
    user_ids: list[int]
    role_ids: list[int]
    created_at: datetime
    updated_at: datetime


class CameraStatusSummary(BaseModel):
    online: int
    offline: int
    unstable: int
    total: int
    generated_at: datetime


class CameraStatusPeriodOut(BaseModel):
    id: int
    camera_id: int
    camera_name: str
    status: Literal["online", "offline", "unstable"]
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
