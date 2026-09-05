import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("PUBLIC_RTMP_BASE_URL", "rtmp://localhost:1935")
os.environ.setdefault("PUBLIC_HLS_BASE_URL", "http://localhost:8888")
os.environ.setdefault("PUBLIC_PLAYBACK_BASE_URL", "http://localhost:9996")
os.environ.setdefault("RECORD_DELETE_AFTER", "1h")
os.environ.setdefault(
    "AUTH_JWT_SECRET", "unit-test-secret-with-at-least-32-characters"
)

from app.services.storage import R2Storage, _parse_segment_start


def test_parse_segment_start_valid_filename():
    key = "live/cam-abc123/2026-09-05_00-15-30-123456.mp4"
    parsed = _parse_segment_start(key)
    assert parsed == datetime(2026, 9, 5, 0, 15, 30, 123456, tzinfo=timezone.utc)


def test_parse_segment_start_rejects_unexpected_filename():
    assert _parse_segment_start("live/cam-abc123/not-a-timestamp.mp4") is None


def test_not_configured_without_all_four_settings(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "r2_account_id", None)
    monkeypatch.setattr(config.settings, "r2_access_key_id", "id")
    monkeypatch.setattr(config.settings, "r2_secret_access_key", None)
    monkeypatch.setattr(config.settings, "r2_bucket_name", "bucket")
    assert R2Storage().is_configured is False


def test_configured_with_all_four_settings(monkeypatch):
    from pydantic import SecretStr

    from app import config

    monkeypatch.setattr(config.settings, "r2_account_id", "test-account")
    monkeypatch.setattr(config.settings, "r2_access_key_id", "test-key")
    monkeypatch.setattr(
        config.settings, "r2_secret_access_key", SecretStr("test-secret")
    )
    monkeypatch.setattr(config.settings, "r2_bucket_name", "test-bucket")
    storage = R2Storage()
    assert storage.is_configured is True
    assert storage._client is not None


def test_upload_and_list_raise_when_not_configured(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "r2_account_id", None)
    storage = R2Storage()
    assert storage.purge_expired(1) == 0
