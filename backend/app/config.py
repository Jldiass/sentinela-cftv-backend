import re

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_version: str = "0.3.1"
    database_url: str = "postgresql+psycopg://cftv:cftv-local@postgres:5432/cftv"
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_playback_url: str = "http://mediamtx:9996"
    public_rtmp_base_url: str = "rtmp://localhost:1935"
    public_hls_base_url: str = "http://localhost:8888"
    public_playback_base_url: str = "http://localhost:9996"
    record_delete_after: str = "1h"
    camera_limit: int = 8
    unstable_after_seconds: int = 20
    api_prefix: str = "/api/v1"
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,http://localhost:8000"
    )
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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

    @property
    def effective_retention_hours(self) -> int:
        match = re.fullmatch(r"(\d+)([hd])", self.record_delete_after)
        assert match is not None
        value = int(match.group(1))
        return value if match.group(2) == "h" else value * 24


settings = Settings()
