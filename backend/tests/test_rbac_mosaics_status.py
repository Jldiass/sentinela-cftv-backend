from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Camera, CameraStatusPeriod, Role
from app.routers.camera_status import csv_safe
from app.services.camera_status import record_statuses
from app.services.mediamtx import mediamtx


def register_admin(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@example.com",
            "full_name": "Administrador",
            "password": "Senha-Forte-123!",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_admin_can_manage_users_roles_and_mosaics(monkeypatch):
    async def fake_statuses():
        return {}

    monkeypatch.setattr(mediamtx, "path_statuses", fake_statuses)
    with TestClient(app) as client:
        admin = register_admin(client)
        roles = client.get("/api/v1/roles", headers=admin)
        assert roles.status_code == 200
        operator = next(item for item in roles.json() if item["name"] == "Operador")

        created_user = client.post(
            "/api/v1/users",
            headers=admin,
            json={
                "email": "operador@example.com",
                "full_name": "Pessoa Operadora",
                "password": "Senha-Operador-123!",
                "role_ids": [operator["id"]],
            },
        )
        assert created_user.status_code == 201

        created_camera = client.post(
            "/api/v1/cameras", headers=admin, json={"name": "Entrada principal"}
        )
        camera_id = created_camera.json()["id"]
        mosaic = client.post(
            "/api/v1/mosaics",
            headers=admin,
            json={
                "name": "Portaria",
                "capacity": 4,
                "cameras": [{"camera_id": camera_id, "position": 1}],
                "role_ids": [operator["id"]],
            },
        )
        assert mosaic.status_code == 201
        assert mosaic.json()["columns"] == 2
        assert mosaic.json()["rows"] == 2
        assert mosaic.json()["camera_count"] == 1
        assert "stream_key" not in mosaic.json()["cameras"][0]["camera"]

        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": "operador@example.com",
                "password": "Senha-Operador-123!",
            },
        )
        operator_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        visible = client.get("/api/v1/mosaics", headers=operator_headers)
        cameras = client.get("/api/v1/cameras", headers=operator_headers)
        forbidden = client.get("/api/v1/users", headers=operator_headers)

    assert visible.status_code == 200
    assert [item["name"] for item in visible.json()] == ["Portaria"]
    assert [item["id"] for item in cameras.json()] == [camera_id]
    assert forbidden.status_code == 403


def test_camera_status_history_and_csv_report(monkeypatch):
    async def fake_statuses():
        return {}

    monkeypatch.setattr(mediamtx, "path_statuses", fake_statuses)
    with TestClient(app) as client:
        headers = register_admin(client)
        camera = client.post(
            "/api/v1/cameras", headers=headers, json={"name": "Garagem"}
        ).json()

        now = datetime.now(timezone.utc)
        with SessionLocal() as db:
            db_camera = db.get(Camera, camera["id"])
            path = f"live/{db_camera.stream_key}"
            assert record_statuses(db, {}, now) in {0, 1}
            assert (
                record_statuses(db, {path: "unstable"}, now + timedelta(seconds=10))
                == 1
            )
            assert (
                record_statuses(db, {path: "online"}, now + timedelta(seconds=30)) == 1
            )
            periods = db.scalars(
                select(CameraStatusPeriod)
                .where(CameraStatusPeriod.camera_id == camera["id"])
                .order_by(CameraStatusPeriod.started_at)
            ).all()
            assert [period.status for period in periods][-3:] == [
                "offline",
                "unstable",
                "online",
            ]

        summary = client.get("/api/v1/camera-status/summary", headers=headers)
        history = client.get("/api/v1/camera-status/history", headers=headers)
        report = client.get("/api/v1/camera-status/report", headers=headers)
        invalid_range = client.get(
            "/api/v1/camera-status/history?from=2026-09-04T13:00:00Z&to=2026-09-04T12:00:00Z",
            headers=headers,
        )

    assert summary.status_code == 200
    assert summary.json()["online"] == 1
    assert history.status_code == 200
    assert {item["status"] for item in history.json()} >= {
        "online",
        "offline",
        "unstable",
    }
    assert report.status_code == 200
    assert report.headers["content-type"].startswith("text/csv")
    assert "Garagem,online" in report.text
    assert invalid_range.status_code == 422


def test_only_first_registration_is_public():
    with TestClient(app) as client:
        register_admin(client)
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "intruso@example.com",
                "full_name": "Usuário sem convite",
                "password": "Senha-Intruso-123!",
            },
        )

    assert response.status_code == 403
    with SessionLocal() as db:
        assert db.scalar(select(Role).where(Role.name == "Administrador")) is not None


def test_last_active_administrator_cannot_remove_own_role():
    with TestClient(app) as client:
        headers = register_admin(client)
        current = client.get("/api/v1/auth/me", headers=headers).json()
        response = client.patch(
            f"/api/v1/users/{current['id']}",
            headers=headers,
            json={"role_ids": []},
        )

    assert response.status_code == 409


def test_csv_export_escapes_spreadsheet_formulas():
    assert csv_safe("=HYPERLINK('https://example.com')").startswith("'=")
    assert csv_safe("Câmera normal") == "Câmera normal"
