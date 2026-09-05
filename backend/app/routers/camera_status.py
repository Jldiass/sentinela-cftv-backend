import csv
import io
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import CameraStatusPeriod, User
from ..schemas import CameraStatusPeriodOut, CameraStatusSummary
from ..services.camera_status import period_duration_seconds
from ..services.rbac import accessible_camera_ids
from .auth import require_permission

router = APIRouter(prefix="/camera-status", tags=["camera-status"])
DbSession = Annotated[Session, Depends(get_db)]
OverviewReader = Annotated[User, Depends(require_permission("overview.read"))]
ReportReader = Annotated[User, Depends(require_permission("reports.read"))]


def validate_range(date_from: datetime | None, date_to: datetime | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(422, "from deve ser anterior a to")


def csv_safe(value: str) -> str:
    return f"'{value}" if value.startswith(("=", "+", "-", "@")) else value


def history_query(
    user: User,
    db: Session,
    camera_id: int | None,
    status_value: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
):
    stmt = select(CameraStatusPeriod).options(joinedload(CameraStatusPeriod.camera))
    allowed = accessible_camera_ids(db, user)
    if allowed is not None:
        stmt = stmt.where(CameraStatusPeriod.camera_id.in_(allowed))
    if camera_id is not None:
        stmt = stmt.where(CameraStatusPeriod.camera_id == camera_id)
    if status_value is not None:
        stmt = stmt.where(CameraStatusPeriod.status == status_value)
    if date_from is not None:
        stmt = stmt.where(
            (CameraStatusPeriod.ended_at.is_(None))
            | (CameraStatusPeriod.ended_at >= date_from)
        )
    if date_to is not None:
        stmt = stmt.where(CameraStatusPeriod.started_at <= date_to)
    return stmt.order_by(CameraStatusPeriod.started_at.desc())


def to_output(period: CameraStatusPeriod):
    return CameraStatusPeriodOut(
        id=period.id,
        camera_id=period.camera_id,
        camera_name=period.camera.name,
        status=period.status,
        started_at=period.started_at,
        ended_at=period.ended_at,
        duration_seconds=period_duration_seconds(period),
    )


@router.get("/summary", response_model=CameraStatusSummary)
def summary(db: DbSession, user: OverviewReader):
    allowed = accessible_camera_ids(db, user)
    stmt = (
        select(CameraStatusPeriod.status, func.count())
        .where(CameraStatusPeriod.ended_at.is_(None))
        .group_by(CameraStatusPeriod.status)
    )
    if allowed is not None:
        stmt = stmt.where(CameraStatusPeriod.camera_id.in_(allowed))
    counts = {name: count for name, count in db.execute(stmt).all()}
    return CameraStatusSummary(
        online=counts.get("online", 0),
        offline=counts.get("offline", 0),
        unstable=counts.get("unstable", 0),
        total=sum(counts.values()),
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/history", response_model=list[CameraStatusPeriodOut])
def history(
    db: DbSession,
    user: ReportReader,
    camera_id: int | None = None,
    status_value: Annotated[
        Literal["online", "offline", "unstable"] | None, Query(alias="status")
    ] = None,
    date_from: Annotated[datetime | None, Query(alias="from")] = None,
    date_to: Annotated[datetime | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
):
    validate_range(date_from, date_to)
    rows = db.scalars(
        history_query(user, db, camera_id, status_value, date_from, date_to).limit(
            limit
        )
    ).all()
    return [to_output(row) for row in rows]


@router.get("/report")
def report(
    db: DbSession,
    user: ReportReader,
    camera_id: int | None = None,
    status_value: Annotated[
        Literal["online", "offline", "unstable"] | None, Query(alias="status")
    ] = None,
    date_from: Annotated[datetime | None, Query(alias="from")] = None,
    date_to: Annotated[datetime | None, Query(alias="to")] = None,
):
    validate_range(date_from, date_to)
    rows = db.scalars(
        history_query(user, db, camera_id, status_value, date_from, date_to).limit(
            10000
        )
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["camera", "status", "inicio", "fim", "duracao_segundos"])
    for row in rows:
        writer.writerow(
            [
                csv_safe(row.camera.name),
                row.status,
                row.started_at.isoformat(),
                row.ended_at.isoformat() if row.ended_at else "",
                period_duration_seconds(row) or "",
            ]
        )
    headers = {"Content-Disposition": 'attachment; filename="conectividade.csv"'}
    return StreamingResponse(
        iter([output.getvalue()]), media_type="text/csv; charset=utf-8", headers=headers
    )
