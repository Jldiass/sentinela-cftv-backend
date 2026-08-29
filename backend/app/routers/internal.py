from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Camera

router = APIRouter(prefix="/internal", include_in_schema=False)
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/mediamtx/auth")
def mediamtx_auth(payload: dict, db: DbSession):
    if payload.get("action") != "publish":
        return Response(status_code=status.HTTP_200_OK)
    camera = db.scalar(
        select(Camera).where(
            Camera.stream_key == payload.get("path", ""), Camera.enabled.is_(True)
        )
    )
    return Response(
        status_code=status.HTTP_200_OK if camera else status.HTTP_401_UNAUTHORIZED
    )
