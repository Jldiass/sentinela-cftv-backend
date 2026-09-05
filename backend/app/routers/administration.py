from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Permission, Role, User
from ..schemas import (
    PermissionOut,
    RoleCreate,
    RoleOut,
    RoleUpdate,
    UserAdminOut,
    UserCreate,
    UserUpdate,
)
from ..services.auth import hash_password, normalize_email, revoke_user_sessions
from ..services.rbac import audit, permission_codes, role_names
from .auth import require_permission

router = APIRouter(tags=["administration"])
DbSession = Annotated[Session, Depends(get_db)]
UserManager = Annotated[User, Depends(require_permission("users.manage"))]
PermissionManager = Annotated[User, Depends(require_permission("permissions.manage"))]


def roles_by_ids(db: Session, ids: list[int]) -> list[Role]:
    unique_ids = set(ids)
    roles = db.scalars(select(Role).where(Role.id.in_(unique_ids))).all()
    if len(roles) != len(unique_ids):
        raise HTTPException(422, "Um ou mais perfis não existem")
    return list(roles)


def permissions_by_codes(db: Session, codes: list[str]) -> list[Permission]:
    unique_codes = set(codes)
    permissions = db.scalars(
        select(Permission).where(Permission.code.in_(unique_codes))
    ).all()
    if len(permissions) != len(unique_codes):
        raise HTTPException(422, "Uma ou mais permissões não existem")
    return list(permissions)


def user_out(user: User) -> UserAdminOut:
    return UserAdminOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
        roles=role_names(user),
        permissions=sorted(permission_codes(user)),
    )


def role_out(role: Role) -> RoleOut:
    return RoleOut(
        id=role.id,
        name=role.name,
        description=role.description,
        permission_codes=sorted(item.code for item in role.permissions),
        is_system=role.is_system,
        user_count=len(role.users),
        created_at=role.created_at,
    )


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(db: DbSession, _: PermissionManager):
    return db.scalars(select(Permission).order_by(Permission.code)).all()


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: DbSession, _: PermissionManager):
    roles = db.scalars(
        select(Role)
        .options(selectinload(Role.permissions), selectinload(Role.users))
        .order_by(Role.name)
    ).all()
    return [role_out(role) for role in roles]


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreate, db: DbSession, actor: PermissionManager):
    role = Role(
        name=payload.name.strip(),
        description=payload.description.strip(),
        permissions=permissions_by_codes(db, payload.permission_codes),
    )
    db.add(role)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe um perfil com esse nome") from exc
    audit(db, actor, "role.create", "role", role.id, {"name": role.name})
    db.commit()
    db.refresh(role)
    return role_out(role)


@router.patch("/roles/{role_id}", response_model=RoleOut)
def update_role(
    role_id: int, payload: RoleUpdate, db: DbSession, actor: PermissionManager
):
    role = db.scalar(
        select(Role)
        .options(selectinload(Role.permissions), selectinload(Role.users))
        .where(Role.id == role_id)
    )
    if not role:
        raise HTTPException(404, "Perfil não encontrado")
    if payload.name is not None:
        if role.is_system and payload.name.strip() != role.name:
            raise HTTPException(409, "Perfis do sistema não podem ser renomeados")
        role.name = payload.name.strip()
    if payload.description is not None:
        role.description = payload.description.strip()
    if payload.permission_codes is not None:
        role.permissions = permissions_by_codes(db, payload.permission_codes)
    audit(db, actor, "role.update", "role", role.id)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe um perfil com esse nome") from exc
    db.refresh(role)
    return role_out(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: DbSession, actor: PermissionManager):
    role = db.scalar(
        select(Role).options(selectinload(Role.users)).where(Role.id == role_id)
    )
    if not role:
        raise HTTPException(404, "Perfil não encontrado")
    if role.is_system:
        raise HTTPException(409, "Perfis do sistema não podem ser excluídos")
    if role.users:
        raise HTTPException(409, "Remova os usuários do perfil antes de excluí-lo")
    audit(db, actor, "role.delete", "role", role.id, {"name": role.name})
    db.delete(role)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users", response_model=list[UserAdminOut])
def list_users(db: DbSession, _: UserManager):
    users = db.scalars(
        select(User).options(selectinload(User.roles)).order_by(User.id)
    ).all()
    return [user_out(user) for user in users]


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: DbSession, actor: UserManager):
    email = normalize_email(str(payload.email))
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "E-mail já cadastrado")
    user = User(
        email=email,
        full_name=" ".join(payload.full_name.split()),
        password_hash=hash_password(payload.password),
        is_active=payload.is_active,
        roles=roles_by_ids(db, payload.role_ids),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "E-mail já cadastrado") from exc
    audit(db, actor, "user.create", "user", user.id, {"email": email})
    db.commit()
    db.refresh(user)
    return user_out(user)


@router.get("/users/{user_id}", response_model=UserAdminOut)
def get_user(user_id: int, db: DbSession, _: UserManager):
    user = db.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    return user_out(user)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def update_user(user_id: int, payload: UserUpdate, db: DbSession, actor: UserManager):
    user = db.scalar(
        select(User).options(selectinload(User.roles)).where(User.id == user_id)
    )
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    if user.id == actor.id and payload.is_active is False:
        raise HTTPException(409, "Você não pode desativar sua própria conta")
    is_admin = "Administrador" in role_names(user)
    requested_roles = (
        roles_by_ids(db, payload.role_ids) if payload.role_ids is not None else None
    )
    will_be_admin = (
        any(role.name == "Administrador" for role in requested_roles)
        if requested_roles is not None
        else is_admin
    )
    will_be_active = (
        payload.is_active if payload.is_active is not None else user.is_active
    )
    if is_admin and (not will_be_admin or not will_be_active):
        admin_count = (
            db.scalar(
                select(func.count())
                .select_from(User)
                .join(User.roles)
                .where(Role.name == "Administrador", User.is_active.is_(True))
            )
            or 0
        )
        if admin_count <= 1:
            raise HTTPException(409, "O último administrador ativo deve ser mantido")
    security_changed = False
    if payload.email is not None:
        user.email = normalize_email(str(payload.email))
    if payload.full_name is not None:
        user.full_name = " ".join(payload.full_name.split())
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
        security_changed = True
    if payload.is_active is not None and payload.is_active != user.is_active:
        user.is_active = payload.is_active
        security_changed = True
    if payload.role_ids is not None:
        user.roles = requested_roles or []
        security_changed = True
    if security_changed:
        user.token_version += 1
        revoke_user_sessions(db, user.id)
    audit(
        db,
        actor,
        "user.update",
        "user",
        user.id,
        {"fields": sorted(payload.model_fields_set)},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "E-mail já cadastrado") from exc
    db.refresh(user)
    return user_out(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: DbSession, actor: UserManager):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Usuário não encontrado")
    if user.id == actor.id:
        raise HTTPException(409, "Você não pode excluir sua própria conta")
    admin_count = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .join(User.roles)
            .where(Role.name == "Administrador", User.is_active.is_(True))
        )
        or 0
    )
    if user.is_active and "Administrador" in role_names(user) and admin_count <= 1:
        raise HTTPException(409, "O último administrador não pode ser excluído")
    audit(db, actor, "user.delete", "user", user.id, {"email": user.email})
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
