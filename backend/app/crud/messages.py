from datetime import datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session, aliased

from app.models import ChatSession, Message


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


def list_chats_by_user(
    db: Session, user_id: int, limit: int, offset: int
) -> tuple[list[dict], int]:
    numbered = (
        select(
            Message,
            func.lead(Message.id)
            .over(partition_by=Message.session_id, order_by=Message.id)
            .label("next_id"),
        )
        .where(Message.user_id == user_id)
        .subquery()
    )
    question = aliased(Message, numbered)
    answer = aliased(Message)
    stmt = (
        select(
            question.id,
            question.session_id,
            ChatSession.title.label("session_title"),
            question.content.label("question"),
            answer.content.label("answer"),
            case((answer.id.is_(None), "error"), else_=answer.status).label("status"),
            func.coalesce(answer.error_code, question.error_code).label("error_code"),
            func.coalesce(answer.model_code, question.model_code).label("model_code"),
            (question.billed_tokens + func.coalesce(answer.billed_tokens, 0)).label(
                "billed_tokens"
            ),
            question.created_at,
        )
        .join(ChatSession, ChatSession.id == question.session_id)
        .outerjoin(answer, and_(answer.id == numbered.c.next_id, answer.role == "assistant"))
        .where(question.role == "user")
        .order_by(question.created_at.desc(), question.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [dict(row) for row in db.execute(stmt).mappings()]
    total = db.scalar(
        select(func.count()).where(Message.user_id == user_id, Message.role == "user")
    )
    return items, total
