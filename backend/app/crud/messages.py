from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models import ChatSession, Message


def list_by_session(db: Session, session_id: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(db.scalars(stmt))


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
            func.coalesce(answer.status, question.status).label("status"),
            answer.error_code,
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
