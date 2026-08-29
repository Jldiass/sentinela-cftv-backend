from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://cftv:cftv-local@postgres:5432/cftv"
    mediamtx_api_url: str = "http://mediamtx:9997"
    mediamtx_playback_url: str = "http://mediamtx:9996"
    public_rtmp_base_url: str = "rtmp://localhost:1935"
    public_hls_base_url: str = "http://localhost:8888"
    public_playback_base_url: str = "http://localhost:9996"
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


settings = Settings()
