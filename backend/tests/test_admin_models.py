from datetime import UTC, datetime, timedelta

import pytest

from app.models import AIModel, ChatSession, Message, User


def signup_login(client, username):
    client.cookies.clear()
    client.post("/api/auth/signup", json={"username": username, "password": "password1"})
    client.post("/api/auth/login", json={"username": username, "password": "password1"})


@pytest.fixture
def admin(client, db):
    signup_login(client, "admin")
    user = db.query(User).filter_by(username="admin").one()
    user.role = "admin"
    db.commit()
    return user


def test_admin_api_requires_admin(client):
    assert client.get("/api/admin/models").status_code == 401
    signup_login(client, "alice")
    res = client.get("/api/admin/models")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "FORBIDDEN"
    assert client.patch("/api/admin/models/gpt-5.5", json={"is_active": False}).status_code == 403
    assert client.get("/api/admin/usage").status_code == 403


def test_list_all_models(client, db, admin):
    db.query(AIModel).filter_by(code="gemini-3-flash").one().is_active = False
    db.commit()

    body = client.get("/api/admin/models").json()

    assert len(body) == 11
    assert body[0]["code"] == "gemini-3-flash"
    assert body[0]["is_active"] is False
    assert body[0]["max_tokens"] == 4096


def test_update_model(client, admin):
    res = client.patch(
        "/api/admin/models/gpt-5.5",
        json={"multiplier": 2.5, "max_tokens": 8000, "sort_order": 0, "is_active": False},
    )

    assert res.status_code == 200
    body = res.json()
    assert (body["multiplier"], body["max_tokens"], body["sort_order"]) == (2.5, 8000, 0)
    assert body["is_active"] is False
    codes = [m["code"] for m in client.get("/api/models").json()]
    assert "gpt-5.5" not in codes


@pytest.mark.parametrize(
    "payload", [{"multiplier": 0}, {"multiplier": 1.234}, {"max_tokens": 0}, {"max_tokens": 32001}]
)
def test_update_model_invalid(client, admin, payload):
    assert client.patch("/api/admin/models/gpt-5.5", json=payload).status_code == 422


def test_update_model_not_found(client, admin):
    res = client.patch("/api/admin/models/unknown", json={"is_active": False})
    assert res.status_code == 404


def test_change_default_model(client, db, admin):
    res = client.patch("/api/admin/models/gpt-5.4", json={"is_default": True})

    assert res.status_code == 200
    defaults = [m["code"] for m in client.get("/api/admin/models").json() if m["is_default"]]
    assert defaults == ["gpt-5.4"]


@pytest.mark.parametrize(
    ("code", "payload"),
    [
        ("gpt-5-mini", {"is_active": False}),
        ("gpt-5-mini", {"is_default": False}),
        ("gpt-5.4", {"is_default": True, "is_active": False}),
    ],
)
def test_default_model_must_stay_active(client, admin, code, payload):
    res = client.patch(f"/api/admin/models/{code}", json=payload)
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "DEFAULT_MODEL_REQUIRED"


def test_usage_by_day(client, db, admin):
    session = ChatSession(user_id=admin.id, title="기록", model_code="gpt-5-mini")
    db.add(session)
    db.flush()
    now = datetime.now(UTC)
    kst_today = (now + timedelta(hours=9)).date()

    def add(model_code, billed, created_at, role="assistant", status="ok"):
        db.add(
            Message(
                session_id=session.id,
                user_id=admin.id,
                role=role,
                content="내용",
                status=status,
                model_code=model_code,
                billed_tokens=billed,
                created_at=created_at,
            )
        )

    add("gpt-5-mini", 10, now)
    add("gpt-5-mini", 20, now)
    add("gpt-5.5", 50, now)
    add("gpt-5-mini", 0, now, status="error")
    add(None, 0, now, role="user")
    add("gpt-5-mini", 7, now - timedelta(days=1))
    add("gpt-5-mini", 99, now - timedelta(days=40))
    db.commit()

    body = client.get("/api/admin/usage", params={"days": 2}).json()

    yesterday = (kst_today - timedelta(days=1)).isoformat()
    today = kst_today.isoformat()
    assert body == [
        {"date": yesterday, "model_code": "gpt-5-mini", "billed_tokens": 7, "requests": 1},
        {"date": today, "model_code": "gpt-5-mini", "billed_tokens": 30, "requests": 2},
        {"date": today, "model_code": "gpt-5.5", "billed_tokens": 50, "requests": 1},
    ]
