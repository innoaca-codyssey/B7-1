from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import EmailVerification


def replace(db: Session, user_id: int, code_hash: str, expires_at: datetime) -> EmailVerification:
    db.execute(delete(EmailVerification).where(EmailVerification.user_id == user_id))
    verification = EmailVerification(user_id=user_id, code_hash=code_hash, expires_at=expires_at)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def get_latest(db: Session, user_id: int) -> EmailVerification | None:
    return db.scalar(
        select(EmailVerification)
        .where(EmailVerification.user_id == user_id)
        .order_by(EmailVerification.id.desc())
    )


def delete_for_user(db: Session, user_id: int) -> None:
    db.execute(delete(EmailVerification).where(EmailVerification.user_id == user_id))
