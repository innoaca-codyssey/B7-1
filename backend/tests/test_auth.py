import pytest
from fastapi import HTTPException

from app.crud import users
from app.deps import require_admin


def test_signup(client):
    res = client.post(
        "/api/auth/signup", json={"username": "alice", "name": " 앨리스 ", "password": "password1"}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "alice"
    assert body["display_name"] == "앨리스"
    assert body["role"] == "user"
    assert "password_hash" not in body


def test_signup_duplicate(client):
    client.post(
        "/api/auth/signup", json={"username": "alice", "name": "사용자", "password": "password1"}
    )
    res = client.post(
        "/api/auth/signup", json={"username": "alice", "name": "사용자", "password": "password2"}
    )
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "USERNAME_TAKEN"


def test_signup_invalid(client):
    for payload in [
        {"username": "Alice", "name": "앨리스", "password": "password1"},
        {"username": "al", "name": "앨리스", "password": "password1"},
        {"username": "alice", "name": "앨리스", "password": "short"},
        {"username": "alice", "name": "앨리스", "password": "가" * 25},
        {"username": "alice", "password": "password1"},
        {"username": "alice", "name": "   ", "password": "password1"},
        {"username": "alice", "name": "가" * 31, "password": "password1"},
    ]:
        assert client.post("/api/auth/signup", json=payload).status_code == 422


def signup_and_login(client, username="alice", password="password1"):
    client.post(
        "/api/auth/signup", json={"username": username, "name": "사용자", "password": password}
    )
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
    client.post(
        "/api/auth/signup", json={"username": "alice", "name": "사용자", "password": "password1"}
    )
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
