from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import settings
from app.crud import users
from app.main import app
from app.security import verify_password


def start_app(monkeypatch, username, password):
    monkeypatch.setattr(settings, "admin_username", username)
    monkeypatch.setattr(settings, "admin_password", SecretStr(password) if password else None)
    with TestClient(app):
        pass


def test_create_admin_on_startup(monkeypatch, db):
    start_app(monkeypatch, "admin", "adminpass1")

    admin = users.get_by_username(db, "admin")
    assert admin.role == "admin"
    assert verify_password("adminpass1", admin.password_hash)


def test_promote_existing_user_keeps_password(monkeypatch, db):
    users.create(db, "alice", "original-hash")

    start_app(monkeypatch, "alice", "newpass123")

    db.expire_all()
    alice = users.get_by_username(db, "alice")
    assert alice.role == "admin"
    assert alice.password_hash == "original-hash"


def test_skip_without_admin_settings(monkeypatch, db):
    start_app(monkeypatch, "admin", None)

    assert users.get_by_username(db, "admin") is None
