def test_signup(client):
    res = client.post("/api/auth/signup", json={"username": "alice", "password": "password1"})
    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "alice"
    assert body["role"] == "user"
    assert "password_hash" not in body


def test_signup_duplicate(client):
    client.post("/api/auth/signup", json={"username": "alice", "password": "password1"})
    res = client.post("/api/auth/signup", json={"username": "alice", "password": "password2"})
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "USERNAME_TAKEN"


def test_signup_invalid(client):
    for payload in [
        {"username": "Alice", "password": "password1"},
        {"username": "al", "password": "password1"},
        {"username": "alice", "password": "short"},
        {"username": "alice", "password": "가" * 25},
    ]:
        assert client.post("/api/auth/signup", json=payload).status_code == 422
