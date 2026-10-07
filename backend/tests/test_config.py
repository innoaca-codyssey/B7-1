import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize("secret", ["", "short-secret"])
def test_jwt_secret_too_short(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret=secret)


def test_jwt_secret_min_length():
    assert Settings(_env_file=None, jwt_secret="x" * 32).jwt_secret == "x" * 32


@pytest.mark.parametrize("password", ["short", "가" * 25])
def test_admin_password_invalid(password):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, jwt_secret="x" * 32, admin_password=password)


def test_admin_password_secret():
    settings = Settings(_env_file=None, jwt_secret="x" * 32, admin_password="adminpass1")
    assert settings.admin_password.get_secret_value() == "adminpass1"
    assert "adminpass1" not in repr(settings)


def test_empty_admin_settings_ignored(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "")
    monkeypatch.setenv("ADMIN_PASSWORD", "")
    settings = Settings(_env_file=None, jwt_secret="x" * 32)
    assert settings.admin_username is None
    assert settings.admin_password is None
