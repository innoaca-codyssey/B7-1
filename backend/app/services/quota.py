import math
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def billed_tokens(input_tokens: int, output_tokens: int, multiplier: Decimal) -> int:
    return math.ceil((input_tokens + output_tokens) * Decimal(str(multiplier)))


def month_start_kst(now: datetime | None = None) -> datetime:
    now = (now or datetime.now(KST)).astimezone(KST)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
