import os
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["PUBLIC_RTMP_BASE_URL"] = "rtmp://localhost:1935"
os.environ["PUBLIC_HLS_BASE_URL"] = "http://localhost:8888"
os.environ["PUBLIC_PLAYBACK_BASE_URL"] = "http://localhost:9996"

from fastapi.testclient import TestClient

from app.main import app
from app.services.mediamtx import mediamtx


def test_camera_event_and_recording_flow(monkeypatch):
    async def fake_statuses():
        return {}

    async def fake_recordings(path, start, end):
        return [{"start": "2026-08-29T02:00:00Z", "duration": 30.5}]

    monkeypatch.setattr(mediamtx, "path_statuses", fake_statuses)
    monkeypatch.setattr(mediamtx, "list_recordings", fake_recordings)

    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True

        created = client.post(
            "/api/v1/cameras",
            json={
                "name": "Entrada",
                "location": "Recepção",
                "audio_enabled": True,
                "retention_days": 7,
                "pre_alarm_seconds": 20,
                "post_alarm_seconds": 40,
            },
        )
        assert created.status_code == 201
        camera = created.json()
        camera_id = camera["id"]
        original_key = camera["stream_key"]

        listed = client.get("/api/v1/cameras")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        updated = client.patch(
            f"/api/v1/cameras/{camera_id}", json={"location": "Portaria"}
        )
        assert updated.status_code == 200
        assert updated.json()["location"] == "Portaria"

        credentials = client.get(f"/api/v1/cameras/{camera_id}/stream")
        assert credentials.status_code == 200
        assert credentials.json()["rtmp_url"].endswith(original_key)

        allowed = client.post(
            "/internal/mediamtx/auth", json={"action": "publish", "path": original_key}
        )
        assert allowed.status_code == 200
        denied = client.post(
            "/internal/mediamtx/auth", json={"action": "publish", "path": "unknown"}
        )
        assert denied.status_code == 401

        event = client.post(
            f"/api/v1/cameras/{camera_id}/events",
            json={
                "kind": "zona-01",
                "note": "Movimento",
                "happened_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert event.status_code == 201
        assert event.json()["clip_duration"] == 60

        recordings = client.get(f"/api/v1/cameras/{camera_id}/recordings")
        assert recordings.status_code == 200
        assert recordings.json()[0]["url"].endswith("format=mp4")

        rotated = client.post(f"/api/v1/cameras/{camera_id}/stream-key/rotate")
        assert rotated.status_code == 200
        assert rotated.json()["stream_key"] != original_key

        deleted = client.delete(f"/api/v1/cameras/{camera_id}")
        assert deleted.status_code == 204
        assert client.get(f"/api/v1/cameras/{camera_id}").status_code == 404


def test_validation_and_not_found(monkeypatch):
    async def fake_statuses():
        return {}

    monkeypatch.setattr(mediamtx, "path_statuses", fake_statuses)
    with TestClient(app) as client:
        assert client.post("/api/v1/cameras", json={"name": "x"}).status_code == 422
        assert client.get("/api/v1/cameras/999999").status_code == 404
        assert client.get("/api/v1/events/999999").status_code == 404
