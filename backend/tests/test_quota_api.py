import logging
from datetime import timedelta

import pytest

from app.models import ChatSession, Message, User
from app.services import ai_client
from app.services.ai_client import AIResult
from app.services.quota import month_start_kst


@pytest.fixture
def user(client, db):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password1"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    return db.query(User).filter_by(username="alice").one()


@pytest.fixture
def ai_calls(monkeypatch):
    calls = []

    def fake_chat(model, messages, max_tokens):
        calls.append(model)
        return AIResult(content="답변", input_tokens=100, output_tokens=51)

    monkeypatch.setattr(ai_client, "chat", fake_chat)
    return calls


def add_usage(db, user, billed, created_at=None):
    session = ChatSession(user_id=user.id, title="기록", model_code="gpt-5-mini")
    db.add(session)
    db.flush()
    db.add(
        Message(
            session_id=session.id,
            user_id=user.id,
            role="assistant",
            content="답변",
            billed_tokens=billed,
            created_at=created_at,
        )
    )
    db.commit()


def test_usage_requires_login(client):
    assert client.get("/api/me/usage").status_code == 401


def test_usage_excludes_last_month(client, db, user):
    add_usage(db, user, 300)
    add_usage(db, user, 5000, month_start_kst() - timedelta(seconds=1))

    res = client.get("/api/me/usage")

    assert res.status_code == 200
    assert res.json() == {"month_used": 300, "token_limit": 100000, "remaining": 99700}


def test_chat_returns_usage(client, db, user, ai_calls):
    add_usage(db, user, 300)

    res = client.post("/api/chat", json={"message": "안녕"})

    assert res.status_code == 200
    assert res.json()["usage"] == {"month_used": 376, "token_limit": 100000, "remaining": 99624}


def test_chat_quota_exceeded(client, db, user, ai_calls, caplog):
    user.token_limit = 1000
    db.commit()
    add_usage(db, user, 1000)
    message_count = db.query(Message).count()

    res = client.post("/api/chat", json={"message": "안녕"})

    assert res.status_code == 429
    assert res.json()["detail"]["code"] == "QUOTA_EXCEEDED"
    assert ai_calls == []
    assert db.query(Message).count() == message_count
    assert any(
        r.levelno == logging.WARNING
        and r.message == f"quota_exceeded user_id={user.id} month_used=1000 token_limit=1000"
        for r in caplog.records
    )
    assert client.get("/api/me/usage").json()["remaining"] == 0
