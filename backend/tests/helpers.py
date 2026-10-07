def register(client, username, password="password1", name="사용자"):
    return client.post(
        "/api/auth/signup",
        json={
            "username": username,
            "name": name,
            "email": f"{username}@example.com",
            "password": password,
        },
    )
