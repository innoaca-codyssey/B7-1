from datetime import UTC, datetime
from decimal import Decimal

from app.services.quota import KST, billed_tokens, month_start_kst


def test_billed_tokens():
    assert billed_tokens(100, 50, Decimal("1.00")) == 150
    assert billed_tokens(100, 51, Decimal("0.50")) == 76
    assert billed_tokens(10, 0, Decimal("1.50")) == 15
    assert billed_tokens(0, 0, Decimal("2.00")) == 0


def test_month_start_kst():
    now = datetime(2026, 10, 7, 9, 30, tzinfo=KST)
    assert month_start_kst(now) == datetime(2026, 10, 1, tzinfo=KST)


def test_month_start_kst_from_utc():
    now = datetime(2026, 9, 30, 16, 0, tzinfo=UTC)
    assert month_start_kst(now) == datetime(2026, 10, 1, tzinfo=KST)
