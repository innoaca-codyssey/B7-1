import logging
from datetime import UTC, datetime

import pytest

from app.crud import sessions, users
from app.models import Message
from app.security import hash_password

NOW = datetime.now(UTC)


@pytest.fixture
def admin(client, db):
    user = users.create(
        db, "admin", hash_password("adminpass1"), role="admin", email_verified_at=NOW
    )
    client.post("/api/auth/login", json={"username": "admin", "password": "adminpass1"})
    return user


def add_pair(db, user, question, answer):
    chat_session = sessions.create(db, user.id, f"{user.username} 대화", "gpt-5-mini", "tutor")
    db.add(Message(session_id=chat_session.id, user_id=user.id, role="user", content=question))
    db.add(Message(session_id=chat_session.id, user_id=user.id, role="assistant", content=answer))
    db.commit()


def test_admin_chats_requires_admin(client, db):
    assert client.get("/api/admin/chats").status_code == 401

    users.create(db, "alice", hash_password("password1"), email_verified_at=NOW)
    client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    assert client.get("/api/admin/chats").status_code == 403


def test_admin_chats_all_and_filter(client, db, admin, caplog):
    caplog.set_level(logging.INFO, logger="app")
    alice = users.create(db, "alice", "hash")
    bob = users.create(db, "bob", "hash")
    add_pair(db, alice, "alice 질문", "alice 답변")
    add_pair(db, bob, "bob 질문", "bob 답변")

    body = client.get("/api/admin/chats").json()
    assert body["total"] == 2
    assert [(i["username"], i["question"], i["answer"]) for i in body["items"]] == [
        ("bob", "bob 질문", "bob 답변"),
        ("alice", "alice 질문", "alice 답변"),
    ]
    assert body["items"][0]["session_title"] == "bob 대화"

    body = client.get("/api/admin/chats", params={"user_id": alice.id}).json()
    assert body["total"] == 1
    assert body["items"][0]["username"] == "alice"
    assert body["items"][0]["name"] == "alice"

    res = client.get("/api/admin/chats", params={"limit": 1, "offset": 1})
    assert [i["username"] for i in res.json()["items"]] == ["alice"]

    assert f"admin_chats_viewed admin_id={admin.id} user_id=all offset=0 limit=50" in (
        caplog.messages
    )
    assert f"admin_chats_viewed admin_id={admin.id} user_id={alice.id} offset=0 limit=50" in (
        caplog.messages
    )
