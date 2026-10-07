import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("secret", ["", "short-secret"])
def test_jwt_secret_too_short(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=secret)


def test_jwt_secret_min_length():
    assert Settings(_env_file=None, jwt_secret="x" * 32).jwt_secret == "x" * 32
