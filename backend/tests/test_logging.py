import logging

from fastapi import Request
from fastapi.testclient import TestClient

from app.logging_config import log_event
from app.main import app


@app.get("/api/test-request-id", include_in_schema=False)
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


def test_log_event_quotes_values(caplog):
    caplog.set_level(logging.INFO, logger="app")
    log_event("event", path="/a b=1\nc", empty="", plain="ok")
    assert caplog.messages == ['event path="/a b=1\\nc" empty="" plain=ok']


def test_request_path_cannot_add_fields(caplog):
    caplog.set_level(logging.INFO, logger="app")
    TestClient(app).get("/api/x%20user_id=1")
    assert caplog.messages[0].startswith('request_received method=GET path="/api/x user_id=1" ')
