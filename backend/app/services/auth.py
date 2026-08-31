import hashlib
import hmac
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from uuid import uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..config import settings
from ..models import RefreshSession, User

password_hash = PasswordHash(
    [Argon2Hasher(memory_cost=19456, time_cost=2, parallelism=1)]
)
dummy_password_hash = password_hash.hash("not-a-real-user-password")


class InvalidAccessToken(ValueError):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def normalize_email(email: str) -> str:
    return email.strip().casefold()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded_hash: str) -> tuple[bool, str | None]:
    return password_hash.verify_and_update(password, encoded_hash)


def burn_password_check(password: str) -> None:
    password_hash.verify(password, dummy_password_hash)


def create_access_token(user: User) -> tuple[str, int]:
    now = now_utc()
    expires = now + timedelta(minutes=settings.auth_access_token_minutes)
    payload = {
        "sub": str(user.id),
        "type": "access",
        "ver": user.token_version,
        "jti": str(uuid4()),
        "iss": settings.auth_jwt_issuer,
        "aud": settings.auth_jwt_audience,
        "iat": now,
        "nbf": now,
        "exp": expires,
    }
    token = jwt.encode(
        payload,
        settings.auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    return token, settings.auth_access_token_minutes * 60


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.auth_jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            audience=settings.auth_jwt_audience,
            issuer=settings.auth_jwt_issuer,
            options={"require": ["sub", "type", "ver", "jti", "iat", "nbf", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidAccessToken from exc
    if payload.get("type") != "access":
        raise InvalidAccessToken
    return payload


def token_digest(token: str, purpose: str) -> str:
    message = f"{purpose}:{token}".encode()
    return hmac.new(
        settings.auth_jwt_secret.get_secret_value().encode(),
        message,
        hashlib.sha256,
    ).hexdigest()


def create_refresh_session(
    user: User, family_id: str | None = None
) -> tuple[str, RefreshSession]:
    raw_token = secrets.token_urlsafe(48)
    session = RefreshSession(
        id=str(uuid4()),
        family_id=family_id or str(uuid4()),
        user_id=user.id,
        token_hash=token_digest(raw_token, "refresh"),
        expires_at=now_utc() + timedelta(days=settings.auth_refresh_token_days),
    )
    return raw_token, session


def revoke_refresh_family(db: Session, family_id: str) -> None:
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.family_id == family_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now_utc())
    )


def revoke_user_sessions(db: Session, user_id: int) -> None:
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now_utc())
    )


def build_password_reset_url(token: str) -> str:
    separator = "&" if "?" in settings.password_reset_frontend_url else "?"
    return f"{settings.password_reset_frontend_url}{separator}token={token}"


def send_password_reset_email(recipient: str, reset_url: str) -> bool:
    if not settings.smtp_host or not settings.smtp_from:
        return False
    message = EmailMessage()
    message["Subject"] = "Recuperação de senha — Malupe Cam"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        "Recebemos uma solicitação para redefinir sua senha.\n\n"
        f"Use este link: {reset_url}\n\n"
        f"O link expira em {settings.password_reset_minutes} minutos e só pode "
        "ser utilizado uma vez. Se você não solicitou, ignore esta mensagem."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(
                settings.smtp_username,
                settings.smtp_password.get_secret_value(),
            )
        smtp.send_message(message)
    return True
