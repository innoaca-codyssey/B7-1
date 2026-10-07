import logging
import math
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import messages
from app.logging_config import log_event
from app.models import User
from app.schemas.chat import UsageOut

KST = ZoneInfo("Asia/Seoul")


def billed_tokens(input_tokens: int, output_tokens: int, multiplier: Decimal) -> int:
    return math.ceil((input_tokens + output_tokens) * Decimal(str(multiplier)))


def month_start_kst(now: datetime | None = None) -> datetime:
    now = (now or datetime.now(KST)).astimezone(KST)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_usage(db: Session, user: User) -> UsageOut:
    month_used = messages.sum_billed_since(db, user.id, month_start_kst())
    return UsageOut(
        month_used=month_used,
        token_limit=user.token_limit,
        remaining=max(user.token_limit - month_used, 0),
    )


def check_quota(db: Session, user: User) -> None:
    usage = get_usage(db, user)
    if usage.month_used >= usage.token_limit:
        log_event(
            "quota_exceeded",
            logging.WARNING,
            user_id=user.id,
            month_used=usage.month_used,
            token_limit=usage.token_limit,
        )
        raise HTTPException(
            status_code=429,
            detail={
                "code": "QUOTA_EXCEEDED",
                "message": "이번 달 사용량을 모두 사용했습니다. 관리자에게 문의해 주세요.",
            },
        )
