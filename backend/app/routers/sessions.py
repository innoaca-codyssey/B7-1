from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import messages, sessions
from app.database import get_db
from app.deps import get_current_user
from app.models import ChatSession, User
from app.schemas.session import MessageOut, SessionCreate, SessionOut, SessionUpdate

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

DEFAULT_TITLE = "새 대화"
DEFAULT_MODEL_CODE = "gpt-5-mini"

Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_or_404(db: Session, session_id: int, user: User) -> ChatSession:
    chat_session = sessions.get_owned(db, session_id, user.id)
    if not chat_session:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "대화를 찾을 수 없습니다."},
        )
    return chat_session


@router.get("", response_model=list[SessionOut])
def list_sessions(db: Db, user: CurrentUser):
    return sessions.list_by_user(db, user.id)


@router.post("", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, db: Db, user: CurrentUser):
    return sessions.create(
        db,
        user.id,
        title=body.title or DEFAULT_TITLE,
        model_code=body.model_code or DEFAULT_MODEL_CODE,
        preset=body.preset,
    )


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: int, body: SessionUpdate, db: Db, user: CurrentUser):
    chat_session = get_owned_or_404(db, session_id, user)
    return sessions.update(db, chat_session, body.model_dump(exclude_unset=True, exclude_none=True))


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Db, user: CurrentUser):
    sessions.delete(db, get_owned_or_404(db, session_id, user))


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def list_messages(session_id: int, db: Db, user: CurrentUser):
    get_owned_or_404(db, session_id, user)
    return messages.list_by_session(db, session_id)
