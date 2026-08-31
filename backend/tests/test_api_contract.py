import os
from uuid import uuid4

import httpx
import pytest

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
pytestmark = pytest.mark.integration


def test_health_contract():
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["database"] == "up"
    assert payload["mediamtx"] == "up"
    assert payload["version"] == "0.3.3"
    assert payload["effective_retention_hours"] == 1


def test_camera_crud_and_publish_authorization():
    name = f"pytest-{uuid4().hex[:8]}"
    created = httpx.post(
        f"{BASE_URL}/api/v1/cameras",
        json={
            "name": name,
            "location": "teste automatizado",
            "audio_enabled": True,
            "pre_alarm_seconds": 15,
            "post_alarm_seconds": 30,
        },
        timeout=5,
    )
    assert created.status_code == 201
    camera = created.json()
    camera_id = camera["id"]
    try:
        assert camera["stream_key"].startswith("cam-")
        assert camera["status"] == "offline"
        assert camera["stream_path"] == f"live/{camera['stream_key']}"
        assert camera["rtmp_url"] == (
            f"{camera['rtmp_server_url']}/{camera['stream_key']}"
        )
        assert camera["rtmp_url"].count(camera["stream_key"]) == 1

        updated = httpx.patch(
            f"{BASE_URL}/api/v1/cameras/{camera_id}",
            json={"location": "local atualizado", "enabled": False},
            timeout=5,
        )
        assert updated.status_code == 200
        assert updated.json()["location"] == "local atualizado"

        denied = httpx.post(
            f"{BASE_URL}/internal/mediamtx/auth",
            json={"action": "publish", "path": camera["stream_path"]},
            timeout=5,
        )
        assert denied.status_code == 401

        enabled = httpx.patch(
            f"{BASE_URL}/api/v1/cameras/{camera_id}", json={"enabled": True}, timeout=5
        )
        assert enabled.status_code == 200
        allowed = httpx.post(
            f"{BASE_URL}/internal/mediamtx/auth",
            json={"action": "publish", "path": camera["stream_path"]},
            timeout=5,
        )
        assert allowed.status_code == 200

        invalid_range = httpx.get(
            f"{BASE_URL}/api/v1/cameras/{camera_id}/recordings",
            params={"start": "2026-08-29T12:00:00Z", "end": "2026-08-29T11:00:00Z"},
            timeout=5,
        )
        assert invalid_range.status_code == 422
    finally:
        deleted = httpx.delete(f"{BASE_URL}/api/v1/cameras/{camera_id}", timeout=5)
        assert deleted.status_code == 204


def test_unknown_resources_return_404():
    assert httpx.get(f"{BASE_URL}/api/v1/cameras/999999", timeout=5).status_code == 404
    assert httpx.get(f"{BASE_URL}/api/v1/events/999999", timeout=5).status_code == 404
