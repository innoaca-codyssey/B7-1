from datetime import timedelta

import pytest

from app.crud import sessions, users
from app.models import Message
from app.security import hash_password


@pytest.fixture
def admin(client, db):
    user = users.create(db, "admin", hash_password("adminpass1"), role="admin")
    client.post("/api/auth/login", json={"username": "admin", "password": "adminpass1"})
    return user


def test_admin_users_requires_admin(client, db):
    assert client.get("/api/admin/users").status_code == 401

    users.create(db, "alice", hash_password("password1"))
    client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    res = client.get("/api/admin/users")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "FORBIDDEN"
    assert client.patch("/api/admin/users/1", json={"role": "admin"}).status_code == 403


def test_list_users_with_stats(client, db, admin):
    alice = users.create(db, "alice", "hash")
    chat_session = sessions.create(db, alice.id, "운영체제", "gpt-5-mini", "tutor")
    last_month = users.month_start_kst() - timedelta(days=1)
    db.add_all(
        [
            Message(
                session_id=chat_session.id,
                user_id=alice.id,
                role="assistant",
                content="a",
                billed_tokens=30,
            ),
            Message(
                session_id=chat_session.id,
                user_id=alice.id,
                role="assistant",
                content="b",
                billed_tokens=100,
                created_at=last_month,
            ),
        ]
    )
    db.commit()

    res = client.get("/api/admin/users")
    assert res.status_code == 200
    body = {u["username"]: u for u in res.json()}
    assert body["alice"]["month_used"] == 30
    assert body["alice"]["session_count"] == 1
    assert body["admin"]["month_used"] == 0
    assert "password_hash" not in body["alice"]


def test_update_user(client, db, admin):
    alice = users.create(db, "alice", "hash")

    res = client.patch(
        f"/api/admin/users/{alice.id}",
        json={"role": "admin", "is_active": False, "token_limit": 5000},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["role"] == "admin"
    assert body["is_active"] is False
    assert body["token_limit"] == 5000
    assert body["session_count"] == 0


def test_update_user_invalid(client, db, admin):
    alice = users.create(db, "alice", "hash")

    assert client.patch("/api/admin/users/9999", json={"role": "user"}).status_code == 404
    for payload in [{"role": "owner"}, {"token_limit": -1}]:
        assert client.patch(f"/api/admin/users/{alice.id}", json=payload).status_code == 422


def test_self_modify_blocked(client, admin):
    for payload in [{"is_active": False}, {"role": "user"}]:
        res = client.patch(f"/api/admin/users/{admin.id}", json=payload)
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "SELF_MODIFY"

    res = client.patch(f"/api/admin/users/{admin.id}", json={"token_limit": 1})
    assert res.status_code == 200
