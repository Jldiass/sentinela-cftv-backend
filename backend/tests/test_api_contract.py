import os
from uuid import uuid4

import httpx
import pytest

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
pytestmark = pytest.mark.integration


def auth_headers():
    email = os.getenv("TEST_AUTH_EMAIL", "integration-admin@example.com")
    password = os.getenv("TEST_AUTH_PASSWORD", "Integration-Admin-123!")
    login = httpx.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=5,
    )
    if login.status_code == 401:
        login = httpx.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={"email": email, "full_name": "Administrador de integração", "password": password},
            timeout=5,
        )
    assert login.status_code in {200, 201}, (
        "Defina TEST_AUTH_EMAIL e TEST_AUTH_PASSWORD para um administrador existente"
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_health_contract():
    response = httpx.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["database"] == "up"
    assert payload["mediamtx"] == "up"
    assert payload["version"] == "0.5.0"
    assert payload["effective_retention_hours"] == 1


def test_camera_crud_and_publish_authorization():
    headers = auth_headers()
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
        headers=headers,
        timeout=5,
    )
    assert created.status_code == 201
    camera = created.json()
    camera_id = camera["id"]
    try:
        assert camera["status"] == "offline"
        assert "stream_key" not in camera
        credentials = httpx.get(
            f"{BASE_URL}/api/v1/cameras/{camera_id}/stream",
            headers=headers,
            timeout=5,
        ).json()
        assert credentials["stream_key"].startswith("cam-")
        assert credentials["stream_path"] == f"live/{credentials['stream_key']}"
        assert credentials["rtmp_url"].count(credentials["stream_key"]) == 1

        updated = httpx.patch(
            f"{BASE_URL}/api/v1/cameras/{camera_id}",
            json={"location": "local atualizado", "enabled": False},
            headers=headers,
            timeout=5,
        )
        assert updated.status_code == 200
        assert updated.json()["location"] == "local atualizado"

        denied = httpx.post(
            f"{BASE_URL}/internal/mediamtx/auth",
            json={"action": "publish", "path": credentials["stream_path"]},
            timeout=5,
        )
        assert denied.status_code == 401

        enabled = httpx.patch(
            f"{BASE_URL}/api/v1/cameras/{camera_id}",
            json={"enabled": True},
            headers=headers,
            timeout=5,
        )
        assert enabled.status_code == 200
        allowed = httpx.post(
            f"{BASE_URL}/internal/mediamtx/auth",
            json={"action": "publish", "path": credentials["stream_path"]},
            timeout=5,
        )
        assert allowed.status_code == 200

        invalid_range = httpx.get(
            f"{BASE_URL}/api/v1/cameras/{camera_id}/recordings",
            params={"start": "2026-08-29T12:00:00Z", "end": "2026-08-29T11:00:00Z"},
            headers=headers,
            timeout=5,
        )
        assert invalid_range.status_code == 422
    finally:
        deleted = httpx.delete(
            f"{BASE_URL}/api/v1/cameras/{camera_id}", headers=headers, timeout=5
        )
        assert deleted.status_code == 204


def test_unknown_resources_return_404():
    headers = auth_headers()
    assert httpx.get(
        f"{BASE_URL}/api/v1/cameras/999999", headers=headers, timeout=5
    ).status_code == 404
    assert httpx.get(
        f"{BASE_URL}/api/v1/events/999999", headers=headers, timeout=5
    ).status_code == 404
