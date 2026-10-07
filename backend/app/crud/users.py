import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.logging_config import log_event
from app.models import User
from app.security import hash_password


class UsernameTakenError(Exception):
    pass


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create(db: Session, username: str, password_hash: str, role: str = "user") -> User:
    user = User(username=username, password_hash=password_hash, role=role)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise UsernameTakenError(username) from e
    db.refresh(user)
    return user


def get(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def ensure_admin(db: Session, username: str, password: str) -> User | None:
    user = get_by_username(db, username)
    if not user:
        return create(db, username, hash_password(password), role="admin")
    if user.role != "admin":
        log_event("admin_seed_skipped", level=logging.WARNING, username=username)
        return None
    return user
