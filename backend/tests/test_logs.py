from app.crud import sessions, users
from app.models import Message


def add_pair(db, chat_session, question, answer=None, **answer_fields):
    db.add(
        Message(
            session_id=chat_session.id, user_id=chat_session.user_id, role="user", content=question
        )
    )
    if answer is not None:
        db.add(
            Message(
                session_id=chat_session.id,
                user_id=chat_session.user_id,
                role="assistant",
                content=answer,
                model_code=chat_session.model_code,
                **answer_fields,
            )
        )
    db.commit()


def login(client, username):
    client.post(
        "/api/auth/signup", json={"username": username, "name": "사용자", "password": "password1"}
    )
    return client.post("/api/auth/login", json={"username": username, "password": "password1"})


def test_my_chats_requires_login(client):
    assert client.get("/api/me/chats").status_code == 401


def test_my_chats_pairs(client, db):
    alice_id = login(client, "alice").json()["id"]
    bob = users.create(db, "bob", "hash")
    first = sessions.create(db, alice_id, "운영체제", "gpt-5-mini", "tutor")
    second = sessions.create(db, alice_id, "네트워크", "gpt-5-mini", "tutor")
    other = sessions.create(db, bob.id, "bob", "gpt-5-mini", "tutor")

    add_pair(db, first, "질문1", "답변1", billed_tokens=30)
    add_pair(db, second, "질문2", "시간 초과", status="error", error_code="AI_TIMEOUT")
    add_pair(db, first, "질문3")
    add_pair(db, other, "bob 질문", "bob 답변")

    res = client.get("/api/me/chats")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 3
    assert [i["question"] for i in body["items"]] == ["질문3", "질문2", "질문1"]

    latest, error, ok = body["items"]
    assert latest["answer"] is None
    assert latest["status"] == "error"
    assert latest["error_code"] is None
    assert error["session_title"] == "네트워크"
    assert error["status"] == "error"
    assert error["error_code"] == "AI_TIMEOUT"
    assert ok["answer"] == "답변1"
    assert ok["status"] == "ok"
    assert ok["model_code"] == "gpt-5-mini"
    assert ok["billed_tokens"] == 30


def test_my_chats_pagination(client, db):
    alice_id = login(client, "alice").json()["id"]
    chat_session = sessions.create(db, alice_id, "운영체제", "gpt-5-mini", "tutor")
    for n in range(3):
        add_pair(db, chat_session, f"질문{n}", f"답변{n}")

    body = client.get("/api/me/chats", params={"limit": 2, "offset": 1}).json()
    assert body["total"] == 3
    assert [i["question"] for i in body["items"]] == ["질문1", "질문0"]
    assert client.get("/api/me/chats", params={"limit": 0}).status_code == 422
