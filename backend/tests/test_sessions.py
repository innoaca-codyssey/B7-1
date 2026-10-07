import pytest

from app.models import Message


@pytest.fixture
def login(client):
    def _login(username):
        client.cookies.clear()
        client.post("/api/auth/signup", json={"username": username, "password": "password1"})
        res = client.post("/api/auth/login", json={"username": username, "password": "password1"})
        return res.json()

    return _login


def test_sessions_require_login(client):
    assert client.get("/api/sessions").status_code == 401


def test_create_session_defaults(client, login):
    login("alice")
    res = client.post("/api/sessions", json={})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "새 대화"
    assert body["model_code"] == "gpt-5-mini"
    assert body["preset"] == "tutor"
    assert body["message_count"] == 0


def test_create_session_invalid_preset(client, login):
    login("alice")
    assert client.post("/api/sessions", json={"preset": "unknown"}).status_code == 422


def test_list_own_sessions_with_message_count(client, login, db):
    login("bob")
    client.post("/api/sessions", json={"title": "bob"})
    alice = login("alice")
    session_id = client.post("/api/sessions", json={"title": "alice"}).json()["id"]
    db.add_all(
        [
            Message(session_id=session_id, user_id=alice["id"], role="user", content="q"),
            Message(session_id=session_id, user_id=alice["id"], role="assistant", content="a"),
        ]
    )
    db.commit()

    res = client.get("/api/sessions")
    assert [s["title"] for s in res.json()] == ["alice"]
    assert res.json()[0]["message_count"] == 2


def test_update_and_delete_session(client, login):
    login("alice")
    session_id = client.post("/api/sessions", json={}).json()["id"]

    body = {"title": "운영체제", "preset": "concept"}
    res = client.patch(f"/api/sessions/{session_id}", json=body)
    assert res.status_code == 200
    assert res.json()["title"] == "운영체제"
    assert res.json()["preset"] == "concept"

    assert client.delete(f"/api/sessions/{session_id}").status_code == 204
    assert client.get("/api/sessions").json() == []


def test_other_users_session_not_found(client, login):
    login("bob")
    session_id = client.post("/api/sessions", json={}).json()["id"]
    login("alice")

    for res in [
        client.patch(f"/api/sessions/{session_id}", json={"title": "x"}),
        client.delete(f"/api/sessions/{session_id}"),
        client.get(f"/api/sessions/{session_id}/messages"),
    ]:
        assert res.status_code == 404
        assert res.json()["detail"]["code"] == "NOT_FOUND"


def test_list_messages(client, login, db):
    alice = login("alice")
    session_id = client.post("/api/sessions", json={}).json()["id"]
    db.add(Message(session_id=session_id, user_id=alice["id"], role="user", content="질문"))
    db.commit()
    db.add(Message(session_id=session_id, user_id=alice["id"], role="assistant", content="답변"))
    db.commit()

    res = client.get(f"/api/sessions/{session_id}/messages")
    assert res.status_code == 200
    assert [m["content"] for m in res.json()] == ["질문", "답변"]
    assert res.json()[1]["status"] == "ok"
