from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import ai_models, messages
from app.models import AIModel
from app.schemas.model import ModelUpdate
from app.services.quota import KST


def update_model(db: Session, code: str, body: ModelUpdate) -> AIModel:
    model = ai_models.get_by_code(db, code)
    if not model:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "모델을 찾을 수 없습니다."},
        )
    fields = body.model_dump(exclude_none=True)
    if model.is_default and fields.get("is_default") is False:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "DEFAULT_MODEL_REQUIRED",
                "message": "기본 모델은 다른 모델을 기본으로 지정해서 변경합니다.",
            },
        )
    is_default = fields.get("is_default", model.is_default)
    is_active = fields.get("is_active", model.is_active)
    if is_default and not is_active:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "DEFAULT_MODEL_REQUIRED",
                "message": "기본 모델은 비활성화할 수 없습니다.",
            },
        )
    return ai_models.update(db, model, fields)


def usage_by_day(db: Session, days: int) -> list:
    today = datetime.now(KST).replace(hour=0, minute=0, second=0, microsecond=0)
    return messages.usage_by_day(db, today - timedelta(days=days - 1))
