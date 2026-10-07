from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import ai_models, messages, sessions
from app.database import get_db
from app.deps import get_current_user
from app.models import ChatSession, User
from app.schemas.session import MessageOut, SessionCreate, SessionOut, SessionUpdate

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

DEFAULT_TITLE = "새 대화"

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


def get_model_code_or_400(db: Session, code: str | None) -> str:
    model = ai_models.get_active(db, code)
    if not model:
        raise HTTPException(
            status_code=400,
            detail={"code": "MODEL_UNAVAILABLE", "message": "사용할 수 없는 모델입니다."},
        )
    return model.code


@router.get("", response_model=list[SessionOut])
def list_sessions(db: Db, user: CurrentUser):
    return sessions.list_by_user(db, user.id)


@router.post("", response_model=SessionOut, status_code=201)
def create_session(body: SessionCreate, db: Db, user: CurrentUser):
    return sessions.create(
        db,
        user.id,
        title=body.title or DEFAULT_TITLE,
        model_code=get_model_code_or_400(db, body.model_code),
        preset=body.preset,
    )


@router.patch("/{session_id}", response_model=SessionOut)
def update_session(session_id: int, body: SessionUpdate, db: Db, user: CurrentUser):
    chat_session = get_owned_or_404(db, session_id, user)
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    if "model_code" in fields:
        fields["model_code"] = get_model_code_or_400(db, fields["model_code"])
    return sessions.update(db, chat_session, fields)


@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: int, db: Db, user: CurrentUser):
    sessions.delete(db, get_owned_or_404(db, session_id, user))


@router.get("/{session_id}/messages", response_model=list[MessageOut])
def list_messages(session_id: int, db: Db, user: CurrentUser):
    get_owned_or_404(db, session_id, user)
    return messages.list_by_session(db, session_id)
