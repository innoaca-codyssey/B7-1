def test_openapi_schema(client):
    res = client.get("/api/openapi.json")

    assert res.status_code == 200
    schema = res.json()
    assert schema["info"]["version"] == "1.0.0"
    for path in ["/api/auth/login", "/api/chat", "/api/sessions", "/api/admin/users"]:
        assert path in schema["paths"]

    declared = {tag["name"] for tag in schema["tags"]}
    for path, operations in schema["paths"].items():
        for method, operation in operations.items():
            assert operation.get("tags"), f"{method.upper()} {path}"
            assert set(operation["tags"]) <= declared, f"{method.upper()} {path}"


def test_docs_pages(client):
    for path in ["/api/docs", "/api/redoc"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
