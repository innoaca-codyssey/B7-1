OUTBOX: dict[str, str] = {}


def register(client, username, password="password1", name="사용자", verify=True):
    email = f"{username}@example.com"
    res = client.post(
        "/api/auth/signup",
        json={"username": username, "name": name, "email": email, "password": password},
    )
    if verify and res.status_code == 201:
        client.post("/api/auth/verify-email", json={"username": username, "code": OUTBOX[email]})
    return res
