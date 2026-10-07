from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import ai_models
from app.database import get_db
from app.deps import require_admin
from app.schemas.model import AdminModelOut, ModelUpdate, UsageRow
from app.services import admin_models

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])

Db = Annotated[Session, Depends(get_db)]


@router.get("/models", response_model=list[AdminModelOut])
def list_models(db: Db):
    return ai_models.list_all(db)


@router.patch("/models/{code}", response_model=AdminModelOut)
def update_model(code: str, body: ModelUpdate, db: Db):
    return admin_models.update_model(db, code, body)


@router.get("/usage", response_model=list[UsageRow])
def get_usage(db: Db, days: Annotated[int, Query(ge=1, le=365)] = 30):
    return admin_models.usage_by_day(db, days)
