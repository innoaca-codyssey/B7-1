import pytest

from app.config import settings
from app.models import ChatSession, Message
from app.services import ai_client
from app.services.ai_client import AIResult


@pytest.fixture
def login(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password1"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password1"})


@pytest.fixture
def ai_calls(monkeypatch):
    calls = []

    def fake_chat(model, messages, max_tokens):
        calls.append({"model": model, "messages": messages, "max_tokens": max_tokens})
        return AIResult(content=f"답변 {len(calls)}", input_tokens=100, output_tokens=51)

    monkeypatch.setattr(ai_client, "chat", fake_chat)
    return calls


def test_chat_requires_login(client, ai_calls):
    assert client.post("/api/chat", json={"message": "안녕"}).status_code == 401
    assert ai_calls == []


@pytest.mark.parametrize("message", ["", "   ", "가" * 4001])
def test_chat_invalid_message(client, login, ai_calls, message):
    assert client.post("/api/chat", json={"message": message}).status_code == 422
    assert ai_calls == []


def test_chat_creates_session(client, login, ai_calls, db):
    question = "  파이썬에서 리스트와 튜플의 차이를 예제와 함께 알려 주세요  "
    res = client.post("/api/chat", json={"message": question})

    assert res.status_code == 200
    body = res.json()
    session = db.get(ChatSession, body["session_id"])
    assert session.title == question.strip()[:30]
    assert session.model_code == "gpt-5-mini"
    assert session.preset == "tutor"
    assert body["user_message"]["content"] == question.strip()
    assistant = body["assistant_message"]
    assert assistant["content"] == "답변 1"
    assert assistant["model_code"] == "gpt-5-mini"
    assert assistant["input_tokens"] == 100
    assert assistant["output_tokens"] == 51
    assert assistant["billed_tokens"] == 76
    assert assistant["latency_ms"] is not None
    assert db.get(Message, assistant["id"]).request_id
    assert ai_calls[0]["model"] == "gpt-5-mini"
    assert ai_calls[0]["max_tokens"] == 4096


def test_chat_uses_recent_context(client, login, ai_calls, db, monkeypatch):
    monkeypatch.setattr(settings, "context_window", 3)
    session_id = client.post("/api/chat", json={"message": "질문 1"}).json()["session_id"]
    client.post("/api/chat", json={"session_id": session_id, "message": "질문 2"})
    session = db.get(ChatSession, session_id)
    db.add(
        Message(
            session_id=session_id,
            user_id=session.user_id,
            role="assistant",
            content="실패",
            status="error",
        )
    )
    db.commit()
    before = session.updated_at

    res = client.post(
        "/api/chat", json={"session_id": session_id, "message": "질문 3", "preset": "debug"}
    )

    assert res.status_code == 200
    sent = ai_calls[-1]["messages"]
    assert sent[0]["role"] == "system"
    assert "디버깅" in sent[0]["content"]
    assert sent[1:] == [
        {"role": "user", "content": "질문 2"},
        {"role": "assistant", "content": "답변 2"},
        {"role": "user", "content": "질문 3"},
    ]
    db.refresh(session)
    assert session.preset == "debug"
    assert session.updated_at > before


def test_chat_unavailable_model(client, login, ai_calls):
    res = client.post("/api/chat", json={"message": "안녕", "model_code": "unknown"})
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "MODEL_UNAVAILABLE"
    assert ai_calls == []


def test_chat_other_users_session(client, login, ai_calls, db):
    session_id = client.post("/api/chat", json={"message": "안녕"}).json()["session_id"]
    client.cookies.clear()
    client.post("/api/auth/signup", json={"username": "bob", "password": "password1"})
    client.post("/api/auth/login", json={"username": "bob", "password": "password1"})

    res = client.post("/api/chat", json={"session_id": session_id, "message": "안녕"})
    assert res.status_code == 404


def test_chat_releases_transaction_during_ai_call(client, login, db, monkeypatch):
    in_transaction = []

    def fake_chat(model, messages, max_tokens):
        in_transaction.append(db.in_transaction())
        return AIResult(content="답변", input_tokens=1, output_tokens=1)

    monkeypatch.setattr(ai_client, "chat", fake_chat)
    session_id = client.post("/api/chat", json={"message": "질문 1"}).json()["session_id"]
    client.post("/api/chat", json={"session_id": session_id, "message": "질문 2"})

    assert in_transaction == [False, False]
