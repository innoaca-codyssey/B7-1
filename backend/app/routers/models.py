from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import ai_models
from app.database import get_db
from app.presets import PRESETS
from app.schemas.model import ModelOut, PresetOut

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=list[ModelOut])
def list_models(db: Annotated[Session, Depends(get_db)]):
    return ai_models.list_active(db)


@router.get("/presets", response_model=list[PresetOut])
def list_presets():
    return list(PRESETS.values())
