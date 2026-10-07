import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.logging_config import log_event
from app.models import ChatSession, Message, User
from app.security import hash_password
from app.services.quota import month_start_kst


class UsernameTakenError(Exception):
    pass


class EmailTakenError(Exception):
    pass


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create(
    db: Session,
    username: str,
    password_hash: str,
    display_name: str | None = None,
    role: str = "user",
    email: str | None = None,
    email_verified_at: datetime | None = None,
) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        display_name=display_name or username,
        role=role,
        email=email,
        email_verified_at=email_verified_at,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.orig.diag.constraint_name == "users_email_key":
            raise EmailTakenError(email) from e
        raise UsernameTakenError(username) from e
    db.refresh(user)
    return user


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def ensure_admin(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if not user:
        return create(db, username, hash_password(password), display_name=username, role="admin")
    if user.role != "admin":
        log_event("admin_seed_skipped", level=logging.WARNING, username=username)
        return None
    return user


def _with_stats():
    month_used = (
        select(func.coalesce(func.sum(Message.billed_tokens), 0))
        .where(Message.user_id == User.id, Message.created_at >= month_start_kst())
        .scalar_subquery()
    )
    session_count = (
        select(func.count(ChatSession.id)).where(ChatSession.user_id == User.id).scalar_subquery()
    )
    return select(User, month_used.label("month_used"), session_count.label("session_count"))


def list_with_stats(db: Session) -> list[tuple[User, int, int]]:
    return [tuple(row) for row in db.execute(_with_stats().order_by(User.id))]


def get_with_stats(db: Session, user_id: int) -> tuple[User, int, int] | None:
    row = db.execute(_with_stats().where(User.id == user_id)).first()
    return tuple(row) if row else None


def update(db: Session, user: User, fields: dict) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
