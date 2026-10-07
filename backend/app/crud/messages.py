from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Message


def list_by_session(db: Session, session_id: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(db.scalars(stmt))


def list_recent_ok(db: Session, session_id: int, limit: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id, Message.status == "ok")
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(limit)
    )
    return list(reversed(db.scalars(stmt).all()))


def create(db: Session, **fields) -> Message:
    message = Message(**fields)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
