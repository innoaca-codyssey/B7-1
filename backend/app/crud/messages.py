from datetime import datetime

from sqlalchemy import func, select
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


def sum_billed_since(db: Session, user_id: int, since: datetime) -> int:
    stmt = select(func.coalesce(func.sum(Message.billed_tokens), 0)).where(
        Message.user_id == user_id, Message.created_at >= since
    )
    return db.scalar(stmt)
