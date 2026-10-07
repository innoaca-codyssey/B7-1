from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import messages
from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas.logs import ChatLogPage

router = APIRouter(prefix="/api/me", tags=["logs"])


@router.get("/chats", response_model=ChatLogPage)
def list_my_chats(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    items, total = messages.list_chats_by_user(db, user.id, limit, offset)
    return {"items": items, "total": total}
