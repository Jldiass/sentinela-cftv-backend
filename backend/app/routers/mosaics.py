import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Camera, Mosaic, MosaicCamera, Role, User
from ..schemas import MosaicCreate, MosaicOut, MosaicUpdate
from ..services.mediamtx import MediaMTXUnavailable, mediamtx
from ..services.presentation import camera_output, stream_path
from ..services.rbac import audit, permission_codes
from .auth import require_permission

router = APIRouter(prefix="/mosaics", tags=["mosaics"])
DbSession = Annotated[Session, Depends(get_db)]
MosaicReader = Annotated[User, Depends(require_permission("mosaics.read"))]
MosaicManager = Annotated[User, Depends(require_permission("mosaics.manage"))]


def dimensions(capacity: int) -> tuple[int, int]:
    columns = math.ceil(math.sqrt(capacity))
    rows = math.ceil(capacity / columns)
    return columns, rows


def load_mosaic(db: Session, mosaic_id: int) -> Mosaic | None:
    return db.scalar(
        select(Mosaic)
        .options(
            selectinload(Mosaic.cameras).selectinload(MosaicCamera.camera),
            selectinload(Mosaic.users),
            selectinload(Mosaic.roles).selectinload(Role.users),
        )
        .where(Mosaic.id == mosaic_id)
    )


def can_access(mosaic: Mosaic, user: User) -> bool:
    if "mosaics.manage" in permission_codes(user):
        return True
    role_ids = {role.id for role in user.roles}
    return user.id in {item.id for item in mosaic.users} or bool(
        role_ids & {role.id for role in mosaic.roles}
    )


def mosaic_or_404(db: Session, mosaic_id: int, user: User) -> Mosaic:
    mosaic = load_mosaic(db, mosaic_id)
    if not mosaic or not can_access(mosaic, user):
        raise HTTPException(404, "Mosaico não encontrado")
    return mosaic


def validate_members(db: Session, payload, capacity: int):
    positions = [item.position for item in payload]
    camera_ids = [item.camera_id for item in payload]
    if len(positions) != len(set(positions)) or len(camera_ids) != len(set(camera_ids)):
        raise HTTPException(422, "Câmeras e posições não podem ser repetidas")
    if any(position > capacity for position in positions):
        raise HTTPException(422, "A posição da câmera excede a capacidade do mosaico")
    cameras = db.scalars(select(Camera).where(Camera.id.in_(set(camera_ids)))).all()
    if len(cameras) != len(set(camera_ids)):
        raise HTTPException(422, "Uma ou mais câmeras não existem")
    return {camera.id: camera for camera in cameras}


def load_users(db: Session, ids: list[int]):
    items = db.scalars(select(User).where(User.id.in_(set(ids)))).all()
    if len(items) != len(set(ids)):
        raise HTTPException(422, "Um ou mais usuários não existem")
    return list(items)


def load_roles(db: Session, ids: list[int]):
    items = db.scalars(select(Role).where(Role.id.in_(set(ids)))).all()
    if len(items) != len(set(ids)):
        raise HTTPException(422, "Um ou mais perfis não existem")
    return list(items)


async def statuses():
    try:
        return await mediamtx.path_statuses()
    except MediaMTXUnavailable:
        return {}


def to_output(mosaic: Mosaic, stream_statuses: dict[str, str]) -> MosaicOut:
    direct_ids = {user.id for user in mosaic.users}
    inherited_ids = {user.id for role in mosaic.roles for user in role.users}
    return MosaicOut(
        id=mosaic.id,
        name=mosaic.name,
        capacity=mosaic.capacity,
        columns=mosaic.columns,
        rows=mosaic.rows,
        active=mosaic.active,
        camera_count=len(mosaic.cameras),
        user_count=len(direct_ids | inherited_ids),
        cameras=[
            {
                "camera_id": slot.camera_id,
                "position": slot.position,
                "camera": camera_output(
                    slot.camera,
                    stream_statuses.get(stream_path(slot.camera.stream_key), "offline"),
                ),
            }
            for slot in mosaic.cameras
        ],
        user_ids=sorted(direct_ids),
        role_ids=sorted(role.id for role in mosaic.roles),
        created_at=mosaic.created_at,
        updated_at=mosaic.updated_at,
    )


@router.get("", response_model=list[MosaicOut])
async def list_mosaics(
    db: DbSession,
    user: MosaicReader,
    search: str = Query(default="", max_length=120),
    include_inactive: bool = Query(default=False),
):
    stmt = select(Mosaic).options(
        selectinload(Mosaic.cameras).selectinload(MosaicCamera.camera),
        selectinload(Mosaic.users),
        selectinload(Mosaic.roles).selectinload(Role.users),
    )
    if search:
        stmt = stmt.where(Mosaic.name.ilike(f"%{search.strip()}%"))
    if not include_inactive:
        stmt = stmt.where(Mosaic.active.is_(True))
    if "mosaics.manage" not in permission_codes(user):
        role_ids = [role.id for role in user.roles]
        rules = [Mosaic.users.any(User.id == user.id)]
        if role_ids:
            rules.append(Mosaic.roles.any(Role.id.in_(role_ids)))
        stmt = stmt.where(or_(*rules))
    rows = db.scalars(stmt.order_by(Mosaic.name)).unique().all()
    stream_statuses = await statuses()
    return [to_output(row, stream_statuses) for row in rows]


@router.post("", response_model=MosaicOut, status_code=status.HTTP_201_CREATED)
async def create_mosaic(payload: MosaicCreate, db: DbSession, actor: MosaicManager):
    camera_map = validate_members(db, payload.cameras, payload.capacity)
    columns, rows = dimensions(payload.capacity)
    mosaic = Mosaic(
        name=payload.name.strip(),
        capacity=payload.capacity,
        columns=columns,
        rows=rows,
        active=payload.active,
        created_by_id=actor.id,
        users=load_users(db, payload.user_ids),
        roles=load_roles(db, payload.role_ids),
    )
    mosaic.cameras = [
        MosaicCamera(camera=camera_map[item.camera_id], position=item.position)
        for item in payload.cameras
    ]
    db.add(mosaic)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe um mosaico com esse nome") from exc
    audit(db, actor, "mosaic.create", "mosaic", mosaic.id, {"name": mosaic.name})
    db.commit()
    mosaic = load_mosaic(db, mosaic.id)
    return to_output(mosaic, await statuses())


@router.get("/{mosaic_id}", response_model=MosaicOut)
async def get_mosaic(mosaic_id: int, db: DbSession, user: MosaicReader):
    return to_output(mosaic_or_404(db, mosaic_id, user), await statuses())


@router.get("/{mosaic_id}/view", response_model=MosaicOut)
async def view_mosaic(mosaic_id: int, db: DbSession, user: MosaicReader):
    mosaic = mosaic_or_404(db, mosaic_id, user)
    if not mosaic.active and "mosaics.manage" not in permission_codes(user):
        raise HTTPException(404, "Mosaico não encontrado")
    return to_output(mosaic, await statuses())


@router.patch("/{mosaic_id}", response_model=MosaicOut)
async def update_mosaic(
    mosaic_id: int, payload: MosaicUpdate, db: DbSession, actor: MosaicManager
):
    mosaic = load_mosaic(db, mosaic_id)
    if not mosaic:
        raise HTTPException(404, "Mosaico não encontrado")
    capacity = payload.capacity if payload.capacity is not None else mosaic.capacity
    members = payload.cameras
    if members is not None:
        camera_map = validate_members(db, members, capacity)
        mosaic.cameras = [
            MosaicCamera(camera=camera_map[item.camera_id], position=item.position)
            for item in members
        ]
    elif any(slot.position > capacity for slot in mosaic.cameras):
        raise HTTPException(422, "Remova câmeras fora da nova capacidade")
    if payload.name is not None:
        mosaic.name = payload.name.strip()
    if payload.capacity is not None:
        mosaic.capacity = capacity
        mosaic.columns, mosaic.rows = dimensions(capacity)
    if payload.active is not None:
        mosaic.active = payload.active
    if payload.user_ids is not None:
        mosaic.users = load_users(db, payload.user_ids)
    if payload.role_ids is not None:
        mosaic.roles = load_roles(db, payload.role_ids)
    audit(
        db,
        actor,
        "mosaic.update",
        "mosaic",
        mosaic.id,
        {"fields": sorted(payload.model_fields_set)},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Já existe um mosaico com esse nome") from exc
    mosaic = load_mosaic(db, mosaic.id)
    return to_output(mosaic, await statuses())


@router.delete("/{mosaic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mosaic(mosaic_id: int, db: DbSession, actor: MosaicManager):
    mosaic = db.get(Mosaic, mosaic_id)
    if not mosaic:
        raise HTTPException(404, "Mosaico não encontrado")
    audit(db, actor, "mosaic.delete", "mosaic", mosaic.id, {"name": mosaic.name})
    db.delete(mosaic)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
