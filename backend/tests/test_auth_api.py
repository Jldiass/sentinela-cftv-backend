from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import PasswordResetToken, RefreshSession, User


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def register(client: TestClient, email: str, password: str = "Senha-Forte-123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Pessoa de Teste", "password": password},
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_register_hashes_password_and_returns_safe_session_cookie():
    email = unique_email("register")
    password = "Senha-Forte-123!"

    with TestClient(app) as client:
        response = register(client, email, password)

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == 900
    assert payload["user"]["email"] == email
    assert "password" not in payload["user"]
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "path=/api/v1/auth" in cookie

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.password_hash != password
        assert user.password_hash.startswith("$argon2id$")
        assert len(user.refresh_sessions) == 1
        assert user.refresh_sessions[0].token_hash not in cookie


def test_duplicate_registration_login_and_me():
    email = unique_email("login")
    password = "Senha-Forte-123!"

    with TestClient(app) as client:
        first = register(client, email, password)
        duplicate = register(client, email.upper(), password)
        wrong = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "senha-incorreta"},
        )
        logged_in = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        current = client.get(
            "/api/v1/auth/me", headers=bearer(logged_in.json()["access_token"])
        )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert wrong.status_code == 401
    assert logged_in.status_code == 200
    assert current.status_code == 200
    assert current.json()["email"] == email


def test_refresh_token_is_rotated_and_reuse_revokes_the_family():
    email = unique_email("rotation")

    with TestClient(app) as client:
        created = register(client, email)
        assert created.status_code == 201
        old_refresh = client.cookies.get("malupe_refresh")

        rotated = client.post("/api/v1/auth/refresh")
        assert rotated.status_code == 200
        new_refresh = client.cookies.get("malupe_refresh")
        assert new_refresh and new_refresh != old_refresh

        with TestClient(app) as attacker:
            attacker.cookies.set("malupe_refresh", old_refresh, path="/api/v1/auth")
            replay = attacker.post("/api/v1/auth/refresh")

        after_replay = client.post("/api/v1/auth/refresh")

    assert replay.status_code == 401
    assert after_replay.status_code == 401


def test_logout_revokes_refresh_token_and_clears_cookie():
    email = unique_email("logout")

    with TestClient(app) as client:
        assert register(client, email).status_code == 201
        logout = client.post("/api/v1/auth/logout")
        refreshed = client.post("/api/v1/auth/refresh")

    assert logout.status_code == 200
    assert logout.json()["message"] == "Sessão encerrada"
    assert "malupe_refresh=" in logout.headers["set-cookie"]
    assert refreshed.status_code == 401


def test_password_recovery_is_generic_single_use_and_revokes_sessions():
    email = unique_email("reset")
    old_password = "Senha-Antiga-123!"
    new_password = "Senha-Nova-456!"

    with TestClient(app) as client:
        created = register(client, email, old_password)
        old_access = created.json()["access_token"]

        unknown = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": unique_email("unknown")},
        )
        requested = client.post("/api/v1/auth/forgot-password", json={"email": email})
        reset_token = requested.json()["debug_reset_token"]
        reset = client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": new_password},
        )
        reused = client.post(
            "/api/v1/auth/reset-password",
            json={"token": reset_token, "new_password": "Outra-Senha-789!"},
        )
        old_me = client.get("/api/v1/auth/me", headers=bearer(old_access))
        old_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": old_password},
        )
        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )

    assert unknown.status_code == 200
    assert requested.status_code == 200
    assert unknown.json()["message"] == requested.json()["message"]
    assert unknown.json()["debug_reset_token"] is None
    assert reset_token
    assert reset.status_code == 200
    assert reused.status_code == 400
    assert old_me.status_code == 401
    assert old_login.status_code == 401
    assert new_login.status_code == 200

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        reset_rows = db.scalars(
            select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
        ).all()
        assert reset_rows and reset_rows[-1].used_at is not None
        sessions = db.scalars(
            select(RefreshSession).where(RefreshSession.user_id == user.id)
        ).all()
        # A sessão criada antes da redefinição foi revogada. A única sessão ativa
        # é a que acabou de ser criada pelo login com a nova senha.
        assert sum(session.revoked_at is None for session in sessions) == 1
        assert any(session.revoked_at is not None for session in sessions)


def test_change_password_and_logout_all_invalidate_access_tokens():
    email = unique_email("change")
    old_password = "Senha-Antiga-123!"
    new_password = "Senha-Nova-456!"

    with TestClient(app) as client:
        created = register(client, email, old_password)
        access = created.json()["access_token"]
        wrong = client.post(
            "/api/v1/auth/change-password",
            headers=bearer(access),
            json={"current_password": "errada", "new_password": new_password},
        )
        changed = client.post(
            "/api/v1/auth/change-password",
            headers=bearer(access),
            json={"current_password": old_password, "new_password": new_password},
        )
        invalidated = client.get("/api/v1/auth/me", headers=bearer(access))
        logged_in = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )
        new_access = logged_in.json()["access_token"]
        all_logged_out = client.post(
            "/api/v1/auth/logout-all", headers=bearer(new_access)
        )
        invalidated_again = client.get("/api/v1/auth/me", headers=bearer(new_access))

    assert wrong.status_code == 401
    assert changed.status_code == 200
    assert invalidated.status_code == 401
    assert logged_in.status_code == 200
    assert all_logged_out.status_code == 200
    assert invalidated_again.status_code == 401


def test_validation_blocks_malformed_email_and_short_password():
    with TestClient(app) as client:
        injection = register(client, "admin@example.com' OR '1'='1", "Senha-123456!")
        short = register(client, unique_email("short"), "curta")

    assert injection.status_code == 422
    assert short.status_code == 422


def test_openapi_publishes_all_authentication_contracts():
    expected = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/logout-all",
        "/api/v1/auth/me",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/change-password",
    }

    with TestClient(app) as client:
        schema = client.get("/openapi.json")

    assert schema.status_code == 200
    assert expected <= set(schema.json()["paths"])
