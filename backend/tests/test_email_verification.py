import logging
from datetime import UTC, datetime, timedelta

from app.crud import users, verifications
from app.services import mailer
from tests.helpers import register


def verify(client, code, **lookup):
    return client.post("/api/auth/verify-email", json={**lookup, "code": code})


def test_signup_sends_code_and_verify(client, outbox):
    register(client, "alice")
    code = outbox["alice@example.com"]
    assert len(code) == 6 and code.isdigit()

    res = verify(client, code, username="alice")
    assert res.status_code == 200
    assert res.json()["email_verified_at"] is not None

    res = verify(client, code, username="alice")
    assert res.json()["detail"]["code"] == "INVALID_CODE"


def test_verify_with_email(client, outbox):
    register(client, "alice")
    res = verify(client, outbox["alice@example.com"], email="ALICE@example.com")
    assert res.status_code == 200


def test_wrong_code_limit(client, db, outbox):
    register(client, "alice")
    code = outbox["alice@example.com"]
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(5):
        res = verify(client, wrong, username="alice")
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "INVALID_CODE"

    res = verify(client, code, username="alice")
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "INVALID_CODE"


def test_expired_code(client, db, outbox):
    register(client, "alice")
    user = users.get_by_username(db, "alice")
    verification = verifications.get_latest(db, user.id)
    verification.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()

    res = verify(client, outbox["alice@example.com"], username="alice")
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "CODE_EXPIRED"


def test_verify_unknown_user(client):
    res = verify(client, "123456", username="nobody")
    assert res.status_code == 400
    assert res.json()["detail"]["code"] == "INVALID_CODE"


def test_verify_requires_identifier(client):
    assert client.post("/api/auth/verify-email", json={"code": "123456"}).status_code == 422
    assert verify(client, "12345", username="alice").status_code == 422


def test_resend_code(client, db, outbox):
    register(client, "alice")
    old_code = outbox["alice@example.com"]
    user = users.get_by_username(db, "alice")
    verification = verifications.get_latest(db, user.id)
    verification.created_at = datetime.now(UTC) - timedelta(seconds=61)
    db.commit()

    assert client.post("/api/auth/resend-code", json={"username": "alice"}).status_code == 204
    new_code = outbox["alice@example.com"]

    res = client.post("/api/auth/resend-code", json={"username": "alice"})
    assert res.status_code == 429
    assert res.json()["detail"]["code"] == "TOO_MANY_REQUESTS"

    if new_code != old_code:
        assert verify(client, old_code, username="alice").status_code == 400
    assert verify(client, new_code, username="alice").status_code == 200


def test_resend_same_response_for_unknown(client, outbox):
    res = client.post("/api/auth/resend-code", json={"email": "nobody@example.com"})
    assert res.status_code == 204
    assert outbox == {}

    res = client.post("/api/auth/resend-code", json={"email": "nobody@example.com"})
    assert res.status_code == 429


def test_resend_skips_mail_within_interval(client, outbox):
    register(client, "alice")
    outbox.clear()

    assert client.post("/api/auth/resend-code", json={"username": "alice"}).status_code == 204
    assert outbox == {}


def test_signup_succeeds_when_mail_fails(client, monkeypatch, caplog):
    def fail(to, code):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(mailer, "send_verification_code", fail)
    caplog.set_level(logging.INFO, logger="app")

    res = register(client, "alice")
    assert res.status_code == 201
    user_id = res.json()["id"]
    assert f"verification_code_send_fail user_id={user_id} error=RuntimeError" in caplog.messages
