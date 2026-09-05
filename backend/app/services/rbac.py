import json

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import AuditLog, Mosaic, MosaicCamera, Permission, Role, User

PERMISSIONS = {
    "overview.read": "Visualizar resumo e conectividade das câmeras",
    "mosaics.read": "Visualizar mosaicos autorizados",
    "mosaics.manage": "Criar, editar e excluir mosaicos",
    "cameras.read": "Visualizar câmeras e gravações autorizadas",
    "cameras.manage": "Cadastrar câmeras e administrar credenciais RTMP",
    "events.read": "Visualizar eventos autorizados",
    "events.manage": "Criar e excluir eventos",
    "reports.read": "Consultar e exportar relatórios",
    "users.manage": "Administrar usuários",
    "permissions.manage": "Administrar perfis e permissões",
    "system.health.read": "Visualizar a saúde dos serviços",
}

DEFAULT_ROLES = {
    "Administrador": set(PERMISSIONS),
    "Operador": {
        "overview.read",
        "mosaics.read",
        "cameras.read",
        "events.read",
        "events.manage",
        "reports.read",
        "system.health.read",
    },
    "Cliente": {
        "overview.read",
        "mosaics.read",
        "cameras.read",
        "events.read",
        "reports.read",
    },
}


def ensure_rbac_catalog(db: Session) -> None:
    permissions = {item.code: item for item in db.scalars(select(Permission)).all()}
    for code, description in PERMISSIONS.items():
        if code not in permissions:
            permissions[code] = Permission(code=code, description=description)
            db.add(permissions[code])
    db.flush()

    roles = {item.name: item for item in db.scalars(select(Role)).all()}
    for name, codes in DEFAULT_ROLES.items():
        role = roles.get(name)
        if role is None:
            role = Role(
                name=name,
                description=f"Perfil padrão {name.lower()} do Malupe Cam",
                is_system=True,
            )
            db.add(role)
            roles[name] = role
        role.permissions = [permissions[code] for code in sorted(codes)]
    db.flush()

    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    admin_users = (
        db.scalar(
            select(func.count())
            .select_from(User)
            .join(User.roles)
            .where(Role.name == "Administrador")
        )
        or 0
    )
    if user_count and not admin_users:
        first_user = db.scalar(select(User).order_by(User.id).limit(1))
        if first_user:
            first_user.roles.append(roles["Administrador"])
    db.commit()


def permission_codes(user: User) -> set[str]:
    return {permission.code for role in user.roles for permission in role.permissions}


def role_names(user: User) -> list[str]:
    return sorted(role.name for role in user.roles)


def is_administrator(user: User) -> bool:
    return "Administrador" in role_names(user)


def accessible_camera_ids(db: Session, user: User) -> set[int] | None:
    if "cameras.manage" in permission_codes(user):
        return None
    role_ids = [role.id for role in user.roles]
    access_rules = [Mosaic.users.any(User.id == user.id)]
    if role_ids:
        access_rules.append(Mosaic.roles.any(Role.id.in_(role_ids)))
    rows = db.scalars(
        select(MosaicCamera.camera_id)
        .join(Mosaic)
        .where(Mosaic.active.is_(True), or_(*access_rules))
        .distinct()
    ).all()
    return set(rows)


def audit(
    db: Session,
    actor: User | None,
    action: str,
    resource_type: str,
    resource_id: str | int = "",
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
        )
    )
