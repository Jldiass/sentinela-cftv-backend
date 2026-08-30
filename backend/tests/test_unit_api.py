import os
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["PUBLIC_RTMP_BASE_URL"] = "rtmp://localhost:1935"
os.environ["PUBLIC_HLS_BASE_URL"] = "http://localhost:8888"
os.environ["PUBLIC_PLAYBACK_BASE_URL"] = "http://localhost:9996"
os.environ["RECORD_DELETE_AFTER"] = "1h"

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.models import Camera, Event
from app.services.mediamtx import mediamtx, parse_path_statuses
from app.services.presentation import event_output


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
        assert health.json()["effective_retention_hours"] == 1

        created = client.post(
            "/api/v1/cameras",
            json={
                "name": "Entrada",
                "location": "Recepção",
                "audio_enabled": True,
                "pre_alarm_seconds": 20,
                "post_alarm_seconds": 40,
            },
        )
        assert created.status_code == 201
        camera = created.json()
        camera_id = camera["id"]
        original_key = camera["stream_key"]
        assert camera["effective_retention_hours"] == 1
        assert camera["stream_path"] == f"live/{original_key}"
        assert camera["rtmp_server_url"] == "rtmp://localhost:1935/live"
        assert camera["rtmp_url"] == f"{camera['rtmp_server_url']}/{original_key}"

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
        stream = credentials.json()
        assert stream["stream_path"] == f"live/{original_key}"
        assert stream["rtmp_server_url"] == "rtmp://localhost:1935/live"
        assert stream["stream_key"] == original_key
        assert stream["rtmp_url"] == f"{stream['rtmp_server_url']}/{original_key}"
        assert stream["rtmp_url"].count(original_key) == 1

        allowed = client.post(
            "/internal/mediamtx/auth",
            json={"action": "publish", "path": f"live/{original_key}"},
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
        assert event.json()["clip_status"] == "pending"
        assert event.json()["playback_url"] is None

        old_event = client.post(
            f"/api/v1/cameras/{camera_id}/events",
            json={
                "kind": "atrasado",
                "happened_at": (
                    datetime.now(timezone.utc) - timedelta(hours=2)
                ).isoformat(),
            },
        )
        assert old_event.status_code == 422

        future_event = client.post(
            f"/api/v1/cameras/{camera_id}/events",
            json={
                "kind": "futuro",
                "happened_at": (
                    datetime.now(timezone.utc) + timedelta(minutes=5)
                ).isoformat(),
            },
        )
        assert future_event.status_code == 422

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
        assert (
            client.post(
                "/api/v1/cameras",
                json={"name": "Entrada", "retention_days": 7},
            ).status_code
            == 422
        )
        assert client.get("/api/v1/cameras/999999").status_code == 404
        assert client.get("/api/v1/events/999999").status_code == 404


def test_event_clip_lifecycle():
    now = datetime.now(timezone.utc)
    camera = Camera(id=1, stream_key="cam-test")

    pending = Event(
        id=1,
        camera_id=1,
        kind="alarm",
        note="",
        happened_at=now,
        clip_start=now,
        clip_duration=60,
    )
    pending_out = event_output(pending, camera)
    assert pending_out.clip_status == "pending"
    assert pending_out.playback_url is None

    available = Event(
        id=2,
        camera_id=1,
        kind="alarm",
        note="",
        happened_at=now - timedelta(minutes=10),
        clip_start=now - timedelta(minutes=11),
        clip_duration=60,
    )
    available_out = event_output(available, camera)
    assert available_out.clip_status == "available"
    assert available_out.playback_url is not None

    expired = Event(
        id=3,
        camera_id=1,
        kind="alarm",
        note="",
        happened_at=now - timedelta(hours=2),
        clip_start=now - timedelta(hours=2),
        clip_duration=60,
    )
    expired_out = event_output(expired, camera)
    assert expired_out.clip_status == "expired"
    assert expired_out.playback_url is None


def test_camera_limit(monkeypatch):
    async def fake_statuses():
        return {}

    monkeypatch.setattr(mediamtx, "path_statuses", fake_statuses)
    with TestClient(app) as client:
        camera_ids = []
        for index in range(8):
            response = client.post(
                "/api/v1/cameras", json={"name": f"Câmera {index + 1}"}
            )
            assert response.status_code == 201
            camera_ids.append(response.json()["id"])

        overflow = client.post("/api/v1/cameras", json={"name": "Câmera 9"})
        assert overflow.status_code == 409

        for camera_id in camera_ids:
            assert client.delete(f"/api/v1/cameras/{camera_id}").status_code == 204


def test_retention_configuration_is_strict():
    assert Settings(record_delete_after="1h").effective_retention_hours == 1
    assert Settings(record_delete_after="2d").effective_retention_hours == 48
    with pytest.raises(ValidationError):
        Settings(record_delete_after="60m")


def test_mediamtx_statuses_support_current_and_legacy_fields():
    now = datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc)
    statuses = parse_path_statuses(
        {
            "items": [
                {
                    "name": "cam-new",
                    "online": True,
                    "onlineTime": "2026-08-29T11:59:50Z",
                },
                {
                    "name": "cam-legacy",
                    "ready": True,
                    "readyTime": "2026-08-29T11:00:00Z",
                },
                {"name": "cam-offline", "online": False},
            ]
        },
        now,
    )
    assert statuses == {"cam-new": "unstable", "cam-legacy": "online"}


def test_openapi_contract_exposes_global_retention_and_clip_state():
    schema = app.openapi()
    camera_create = schema["components"]["schemas"]["CameraCreate"]["properties"]
    camera_out = schema["components"]["schemas"]["CameraOut"]["properties"]
    event_out = schema["components"]["schemas"]["EventOut"]["properties"]

    assert "retention_days" not in camera_create
    assert "retention_hours" not in camera_create
    assert "effective_retention_hours" in camera_out
    assert "stream_path" in camera_out
    assert "rtmp_server_url" in camera_out
    assert "clip_status" in event_out
    assert "available_until" in event_out
