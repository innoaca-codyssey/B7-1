import logging

from fastapi import Request
from fastapi.testclient import TestClient

from app.main import app


@app.get("/api/test-request-id")
def read_request_id(request: Request):
    return {"request_id": request.state.request_id}


def test_request_received_log(caplog):
    caplog.set_level(logging.INFO, logger="app")
    res = TestClient(app).get("/api/test-request-id")

    request_id = res.json()["request_id"]
    assert len(request_id) == 12
    assert f"request_received method=GET path=/api/test-request-id request_id={request_id}" in (
        caplog.messages
    )
