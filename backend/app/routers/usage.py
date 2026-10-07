from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.chat import UsageOut
from app.services import quota

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("/usage", response_model=UsageOut)
def get_my_usage(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    return quota.get_usage(db, user)
