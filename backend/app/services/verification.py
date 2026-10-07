import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.crud import verifications
from app.logging_config import log_event
from app.models import User
from app.services import mailer

CODE_TTL = timedelta(minutes=10)
MAX_ATTEMPTS = 5
RESEND_INTERVAL_SECONDS = 60

_last_resend: dict[str, float] = {}


class InvalidCodeError(Exception):
    pass


class CodeExpiredError(Exception):
    pass


class TooManyAttemptsError(Exception):
    pass


class TooManyRequestsError(Exception):
    pass


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def issue_code(db: Session, user: User) -> None:
    code = f"{secrets.randbelow(10**6):06d}"
    verifications.replace(db, user.id, _hash(code), datetime.now(UTC) + CODE_TTL)
    try:
        mailer.send_verification_code(user.email, code)
    except Exception as e:
        log_event("verification_code_send_fail", user_id=user.id, error=type(e).__name__)


def verify_code(db: Session, user: User | None, code: str) -> User:
    verification = verifications.get_latest(db, user.id, for_update=True) if user else None
    if not user or user.email_verified_at or not verification:
        raise InvalidCodeError
    if verification.attempts >= MAX_ATTEMPTS:
        raise TooManyAttemptsError
    if verification.expires_at < datetime.now(UTC):
        raise CodeExpiredError
    if not hmac.compare_digest(verification.code_hash, _hash(code)):
        verification.attempts += 1
        db.commit()
        raise InvalidCodeError
    user.email_verified_at = datetime.now(UTC)
    verifications.delete_for_user(db, user.id)
    db.commit()
    db.refresh(user)
    return user


def resend_code(db: Session, identifier: str, user: User | None) -> None:
    now = time.monotonic()
    for key, requested_at in list(_last_resend.items()):
        if now - requested_at >= RESEND_INTERVAL_SECONDS:
            del _last_resend[key]
    if identifier in _last_resend:
        raise TooManyRequestsError
    _last_resend[identifier] = now
    if not user or user.email_verified_at or not user.email:
        return
    latest = verifications.get_latest(db, user.id)
    if latest and datetime.now(UTC) - latest.created_at < timedelta(
        seconds=RESEND_INTERVAL_SECONDS
    ):
        return
    issue_code(db, user)
