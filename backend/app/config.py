import re
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_version: str = "0.5.0"
    database_url: str = "postgresql+psycopg://cftv:cftv-local@postgres:5432/cftv"
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_playback_url: str = "http://mediamtx:9996"
    public_rtmp_base_url: str = "rtmp://localhost:1935"
    rtmp_app_name: str = "live"
    public_hls_base_url: str = "http://localhost:8888"
    public_playback_base_url: str = "http://localhost:9996"
    record_delete_after: str = "1h"
    camera_limit: int = 8
    unstable_after_seconds: int = 20
    status_poll_seconds: int = Field(default=10, ge=5, le=60)
    api_prefix: str = "/api/v1"
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    )
    auth_jwt_secret: SecretStr
    auth_jwt_issuer: str = "malupe-cam"
    auth_jwt_audience: str = "malupe-cam-web"
    auth_access_token_minutes: int = Field(default=15, ge=5, le=60)
    auth_refresh_token_days: int = Field(default=30, ge=1, le=90)
    auth_cookie_name: str = "malupe_refresh"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "strict"
    auth_cookie_domain: str | None = None
    auth_max_failed_logins: int = Field(default=5, ge=3, le=20)
    auth_lock_minutes: int = Field(default=15, ge=1, le=1440)
    password_reset_minutes: int = Field(default=30, ge=5, le=120)
    password_reset_frontend_url: str = "http://localhost:5173/reset-password"
    auth_debug_return_reset_token: bool = False
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True
    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket_name: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def r2_endpoint_url(self) -> str | None:
        if not self.r2_account_id:
            return None
        return f"https://{self.r2_account_id}.r2.cloudflarestorage.com"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @staticmethod
    def clean_base_url(value: str) -> str:
        return value.rstrip("/")

    @field_validator("record_delete_after")
    @classmethod
    def validate_record_delete_after(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[1-9]\d*[hd]", normalized):
            raise ValueError("use horas ou dias; exemplos: 1h ou 7d")
        return normalized

    @field_validator("auth_jwt_secret")
    @classmethod
    def validate_auth_jwt_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < 32:
            raise ValueError("AUTH_JWT_SECRET deve ter pelo menos 32 caracteres")
        return value

    @model_validator(mode="after")
    def validate_cookie_security(self):
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SAMESITE=none exige AUTH_COOKIE_SECURE=true")
        return self

    @property
    def effective_retention_hours(self) -> int:
        match = re.fullmatch(r"(\d+)([hd])", self.record_delete_after)
        assert match is not None
        value = int(match.group(1))
        return value if match.group(2) == "h" else value * 24


settings = Settings()
