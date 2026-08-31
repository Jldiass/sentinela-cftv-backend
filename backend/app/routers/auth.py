import secrets
from datetime import timedelta
from typing import Annotated
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import PasswordResetToken, RefreshSession, User
from ..schemas import (
    AuthOut,
    ChangePasswordRequest,
    ForgotPasswordOut,
    ForgotPasswordRequest,
    LoginRequest,
    MessageOut,
    RegisterRequest,
    ResetPasswordRequest,
    UserOut,
)
from ..services.auth import (
    InvalidAccessToken,
    build_password_reset_url,
    burn_password_check,
    create_access_token,
    create_refresh_session,
    decode_access_token,
    ensure_utc,
    hash_password,
    normalize_email,
    now_utc,
    revoke_refresh_family,
    revoke_user_sessions,
    send_password_reset_email,
    token_digest,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)
REFRESH_COOKIE_PATH = f"{settings.api_prefix}/auth"
GENERIC_RESET_MESSAGE = (
    "Se o e-mail estiver cadastrado, enviaremos as instruções de recuperação."
)


def unauthorized(detail: str = "Credenciais inválidas") -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=raw_token,
        max_age=settings.auth_refresh_token_days * 24 * 60 * 60,
        path=REFRESH_COOKIE_PATH,
        domain=settings.auth_cookie_domain,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    response.headers["Cache-Control"] = "no-store"


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path=REFRESH_COOKIE_PATH,
        domain=settings.auth_cookie_domain,
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,
    )
    response.headers["Cache-Control"] = "no-store"


def auth_output(user: User) -> AuthOut:
    access_token, expires_in = create_access_token(user)
    return AuthOut(
        access_token=access_token,
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


def issue_session(db: Session, response: Response, user: User) -> AuthOut:
    raw_token, refresh_session = create_refresh_session(user)
    db.add(refresh_session)
    db.commit()
    set_refresh_cookie(response, raw_token)
    return auth_output(user)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: DbSession,
) -> User:
    if not credentials or credentials.scheme.casefold() != "bearer":
        raise unauthorized("Token de acesso ausente")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
        token_version = int(payload["ver"])
    except (InvalidAccessToken, KeyError, TypeError, ValueError) as exc:
        raise unauthorized("Token de acesso inválido ou expirado") from exc
    user = db.get(User, user_id)
    if not user or not user.is_active or user.token_version != token_version:
        raise unauthorized("Sessão inválida")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=AuthOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: DbSession):
    email = normalize_email(str(payload.email))
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado") from exc
    return issue_session(db, response, user)


@router.post("/login", response_model=AuthOut)
def login(payload: LoginRequest, response: Response, db: DbSession):
    email = normalize_email(str(payload.email))
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        burn_password_check(payload.password)
        raise unauthorized()
    now = now_utc()
    if user.locked_until and ensure_utc(user.locked_until) > now:
        retry_after = int((ensure_utc(user.locked_until) - now).total_seconds())
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Muitas tentativas. Tente novamente mais tarde.",
            headers={"Retry-After": str(max(1, retry_after))},
        )
    verified, updated_hash = verify_password(payload.password, user.password_hash)
    if not verified:
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.auth_max_failed_logins:
            user.locked_until = now + timedelta(minutes=settings.auth_lock_minutes)
            user.failed_login_attempts = 0
        db.commit()
        raise unauthorized()
    if not user.is_active:
        raise unauthorized("Usuário desativado")
    if updated_hash:
        user.password_hash = updated_hash
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.flush()
    return issue_session(db, response, user)


@router.post("/refresh", response_model=AuthOut)
def refresh(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[
        str | None, Cookie(alias=settings.auth_cookie_name)
    ] = None,
):
    if not refresh_token:
        clear_refresh_cookie(response)
        raise unauthorized("Refresh token ausente")
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_digest(refresh_token, "refresh")
        )
    )
    if not session:
        clear_refresh_cookie(response)
        raise unauthorized("Refresh token inválido")
    now = now_utc()
    if session.revoked_at:
        revoke_refresh_family(db, session.family_id)
        db.commit()
        clear_refresh_cookie(response)
        raise unauthorized("Sessão revogada")
    if ensure_utc(session.expires_at) <= now:
        session.revoked_at = now
        db.commit()
        clear_refresh_cookie(response)
        raise unauthorized("Refresh token expirado")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        session.revoked_at = now
        db.commit()
        clear_refresh_cookie(response)
        raise unauthorized("Usuário desativado")
    raw_token, replacement = create_refresh_session(user, session.family_id)
    db.add(replacement)
    session.revoked_at = now
    session.replaced_by_id = replacement.id
    db.commit()
    set_refresh_cookie(response, raw_token)
    return auth_output(user)


@router.post("/logout", response_model=MessageOut)
def logout(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[
        str | None, Cookie(alias=settings.auth_cookie_name)
    ] = None,
):
    if refresh_token:
        session = db.scalar(
            select(RefreshSession).where(
                RefreshSession.token_hash == token_digest(refresh_token, "refresh")
            )
        )
        if session and not session.revoked_at:
            session.revoked_at = now_utc()
            db.commit()
    clear_refresh_cookie(response)
    return MessageOut(message="Sessão encerrada")


@router.post("/logout-all", response_model=MessageOut)
def logout_all(response: Response, user: CurrentUser, db: DbSession):
    revoke_user_sessions(db, user.id)
    user.token_version += 1
    db.commit()
    clear_refresh_cookie(response)
    return MessageOut(message="Todas as sessões foram encerradas")


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/forgot-password", response_model=ForgotPasswordOut)
def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
):
    email = normalize_email(str(payload.email))
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    raw_token = None
    if user:
        one_hour_ago = now_utc() - timedelta(hours=1)
        recent_count = (
            db.scalar(
                select(func.count())
                .select_from(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.created_at >= one_hour_ago,
                )
            )
            or 0
        )
        if recent_count < 3:
            now = now_utc()
            db.execute(
                update(PasswordResetToken)
                .where(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.used_at.is_(None),
                )
                .values(used_at=now)
            )
            raw_token = secrets.token_urlsafe(48)
            db.add(
                PasswordResetToken(
                    id=str(uuid4()),
                    user_id=user.id,
                    token_hash=token_digest(raw_token, "password-reset"),
                    expires_at=now + timedelta(minutes=settings.password_reset_minutes),
                )
            )
            db.commit()
            if settings.smtp_host and settings.smtp_from:
                background_tasks.add_task(
                    send_password_reset_email,
                    user.email,
                    build_password_reset_url(raw_token),
                )
    return ForgotPasswordOut(
        message=GENERIC_RESET_MESSAGE,
        debug_reset_token=(
            raw_token if settings.auth_debug_return_reset_token else None
        ),
    )


@router.post("/reset-password", response_model=MessageOut)
def reset_password(payload: ResetPasswordRequest, db: DbSession):
    token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash
            == token_digest(payload.token, "password-reset")
        )
    )
    now = now_utc()
    if not token or token.used_at or ensure_utc(token.expires_at) <= now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token inválido ou expirado")
    user = db.get(User, token.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Token inválido ou expirado")
    if verify_password(payload.new_password, user.password_hash)[0]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A nova senha deve ser diferente da atual",
        )
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    user.failed_login_attempts = 0
    user.locked_until = None
    token.used_at = now
    revoke_user_sessions(db, user.id)
    db.commit()
    return MessageOut(message="Senha redefinida. Faça login novamente.")


@router.post("/change-password", response_model=MessageOut)
def change_password(
    payload: ChangePasswordRequest,
    response: Response,
    user: CurrentUser,
    db: DbSession,
):
    if not verify_password(payload.current_password, user.password_hash)[0]:
        raise unauthorized("Senha atual incorreta")
    if verify_password(payload.new_password, user.password_hash)[0]:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "A nova senha deve ser diferente da atual",
        )
    user.password_hash = hash_password(payload.new_password)
    user.token_version += 1
    revoke_user_sessions(db, user.id)
    db.commit()
    clear_refresh_cookie(response)
    return MessageOut(message="Senha alterada. Faça login novamente.")
