import pytest
from fastapi import HTTPException

from app.crud import users
from app.deps import require_admin
from tests.helpers import register


def signup_payload(**fields):
    return {
        "username": "alice",
        "name": "앨리스",
        "email": "alice@example.com",
        "password": "password1",
        **fields,
    }


def test_signup(client):
    res = client.post(
        "/api/auth/signup", json=signup_payload(name=" 앨리스 ", email="Alice@Example.COM")
    )
    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "alice"
    assert body["display_name"] == "앨리스"
    assert body["email"] == "alice@example.com"
    assert body["email_verified_at"] is None
    assert body["role"] == "user"
    assert "password_hash" not in body


def test_signup_duplicate(client):
    client.post("/api/auth/signup", json=signup_payload())

    res = client.post("/api/auth/signup", json=signup_payload(email="other@example.com"))
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "USERNAME_TAKEN"

    res = client.post(
        "/api/auth/signup", json=signup_payload(username="bob", email="ALICE@example.com")
    )
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "EMAIL_TAKEN"


def test_signup_invalid(client):
    for fields in [
        {"username": "Alice"},
        {"username": "al"},
        {"password": "short"},
        {"password": "가" * 25},
        {"name": None},
        {"name": "   "},
        {"name": "가" * 31},
        {"email": None},
        {"email": "not-an-email"},
    ]:
        payload = {k: v for k, v in signup_payload(**fields).items() if v is not None}
        assert client.post("/api/auth/signup", json=payload).status_code == 422


def signup_and_login(client, username="alice", password="password1"):
    register(client, username, password)
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_login_sets_cookie(client):
    res = signup_and_login(client)
    assert res.status_code == 200
    assert res.json()["username"] == "alice"
    cookie = res.headers["set-cookie"]
    assert "access_token=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_login_wrong_password(client):
    register(client, "alice")
    res = client.post("/api/auth/login", json={"username": "alice", "password": "wrongpass"})
    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "INVALID_CREDENTIALS"


def test_me_requires_login(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"]["code"] == "UNAUTHORIZED"


def test_me_and_logout(client):
    signup_and_login(client)
    assert client.get("/api/auth/me").json()["username"] == "alice"

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_invalid_token(client):
    client.cookies.set("access_token", "invalid")
    assert client.get("/api/auth/me").status_code == 401


def test_disabled_user(client, db):
    signup_and_login(client)
    user = users.get_by_username(db, "alice")
    user.is_active = False
    db.commit()

    res = client.get("/api/auth/me")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "USER_DISABLED"

    client.cookies.clear()
    res = client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "USER_DISABLED"


def test_require_admin(db):
    user = users.create(db, "alice", "hash")
    with pytest.raises(HTTPException) as exc:
        require_admin(user)
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "FORBIDDEN"

    user.role = "admin"
    assert require_admin(user) is user


def test_disabled_user_blocked_from_api(client, db):
    signup_and_login(client)
    user = users.get_by_username(db, "alice")
    user.is_active = False
    db.commit()

    for res in [client.get("/api/sessions"), client.get("/api/me/chats")]:
        assert res.status_code == 403
        assert res.json()["detail"]["code"] == "USER_DISABLED"


def test_login_requires_verified_email(client):
    register(client, "alice", verify=False)
    res = client.post("/api/auth/login", json={"username": "alice", "password": "password1"})
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "EMAIL_NOT_VERIFIED"

    res = client.post("/api/auth/login", json={"username": "alice", "password": "wrongpass"})
    assert res.status_code == 401
