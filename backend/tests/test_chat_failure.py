import logging

import pytest
from sqlalchemy.exc import OperationalError

from app.crud import messages
from app.models import ChatSession, Message
from app.services import ai_client
from app.services.ai_client import AIError, AIResult


@pytest.fixture
def login(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password1"})
    client.post("/api/auth/login", json={"username": "alice", "password": "password1"})


def fail_with(monkeypatch, code):
    def fake_chat(model, messages, max_tokens):
        raise AIError(code)

    monkeypatch.setattr(ai_client, "chat", fake_chat)


def answer_with(monkeypatch, sent):
    def fake_chat(model, messages, max_tokens):
        sent.extend(messages)
        return AIResult(content="답변", input_tokens=1, output_tokens=1)

    monkeypatch.setattr(ai_client, "chat", fake_chat)


@pytest.mark.parametrize(("code", "status"), [("AI_TIMEOUT", 504), ("AI_ERROR", 502)])
def test_chat_ai_failure(client, login, db, monkeypatch, caplog, code, status):
    fail_with(monkeypatch, code)

    res = client.post("/api/chat", json={"message": "긴 글 요약해줘"})

    assert res.status_code == status
    detail = res.json()["detail"]
    assert detail["code"] == code
    assert detail["message"]
    session = db.get(ChatSession, detail["session_id"])
    user_message, assistant_message = db.query(Message).filter_by(session_id=session.id).all()
    assert (user_message.status, user_message.error_code) == ("error", code)
    assert assistant_message.status == "error"
    assert assistant_message.error_code == code
    assert assistant_message.content == detail["message"]
    assert assistant_message.request_id
    assert assistant_message.latency_ms is not None
    assert assistant_message.billed_tokens == 0
    assert any(
        r.levelno == logging.WARNING
        and r.message.startswith("ai_call_fail request_id=")
        and f"error_code={code}" in r.message
        for r in caplog.records
    )


def test_failed_turn_excluded_from_context(client, login, monkeypatch):
    fail_with(monkeypatch, "AI_TIMEOUT")
    res = client.post("/api/chat", json={"message": "실패한 질문"})
    session_id = res.json()["detail"]["session_id"]

    sent = []
    answer_with(monkeypatch, sent)
    res = client.post("/api/chat", json={"session_id": session_id, "message": "다시 질문"})

    assert res.status_code == 200
    assert [m["content"] for m in sent[1:]] == ["다시 질문"]


def test_chat_db_save_failure(client, login, db, monkeypatch, caplog):
    sent = []
    answer_with(monkeypatch, sent)
    create = messages.create

    def failing_create(db, **fields):
        if fields["role"] == "assistant":
            raise OperationalError("INSERT", {}, Exception("connection lost"))
        return create(db, **fields)

    monkeypatch.setattr(messages, "create", failing_create)

    res = client.post("/api/chat", json={"message": "저장 실패 질문"})

    assert res.status_code == 500
    detail = res.json()["detail"]
    assert detail["code"] == "DB_ERROR"
    question = db.query(Message).filter_by(session_id=detail["session_id"]).one()
    assert (question.status, question.error_code) == ("error", "DB_ERROR")
    assert any(
        r.levelno == logging.ERROR and r.message.startswith("db_save_fail user_id=")
        for r in caplog.records
    )

    monkeypatch.setattr(messages, "create", create)
    sent.clear()
    payload = {"session_id": detail["session_id"], "message": "다시 질문"}
    res = client.post("/api/chat", json=payload)
    assert res.status_code == 200
    assert [m["content"] for m in sent[1:]] == ["다시 질문"]
