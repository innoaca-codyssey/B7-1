from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, aliased

from app.models import ChatSession, Message, User


def list_by_session(db: Session, session_id: int) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
    )
    return list(db.scalars(stmt))


def list_chats(
    db: Session, limit: int, offset: int, user_id: int | None = None
) -> tuple[list[dict], int]:
    numbered = select(
        Message,
        func.lead(Message.id)
        .over(partition_by=Message.session_id, order_by=Message.id)
        .label("next_id"),
    )
    total_stmt = select(func.count()).where(Message.role == "user")
    if user_id is not None:
        numbered = numbered.where(Message.user_id == user_id)
        total_stmt = total_stmt.where(Message.user_id == user_id)
    numbered = numbered.subquery()
    question = aliased(Message, numbered)
    answer = aliased(Message)
    stmt = (
        select(
            question.id,
            question.session_id,
            ChatSession.title.label("session_title"),
            User.username,
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
        .join(User, User.id == question.user_id)
        .outerjoin(answer, and_(answer.id == numbered.c.next_id, answer.role == "assistant"))
        .where(question.role == "user")
        .order_by(question.created_at.desc(), question.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [dict(row) for row in db.execute(stmt).mappings()]
    return items, db.scalar(total_stmt)
