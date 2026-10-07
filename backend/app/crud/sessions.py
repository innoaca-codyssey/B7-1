from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatSession


def list_by_user(db: Session, user_id: int) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
    )
    return list(db.scalars(stmt))


def get_owned(db: Session, session_id: int, user_id: int) -> ChatSession | None:
    return db.scalar(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
    )


def create(db: Session, user_id: int, title: str, model_code: str, preset: str) -> ChatSession:
    chat_session = ChatSession(user_id=user_id, title=title, model_code=model_code, preset=preset)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def update(db: Session, chat_session: ChatSession, fields: dict) -> ChatSession:
    for key, value in fields.items():
        setattr(chat_session, key, value)
    db.commit()
    db.refresh(chat_session)
    return chat_session


def delete(db: Session, chat_session: ChatSession) -> None:
    db.delete(chat_session)
    db.commit()
