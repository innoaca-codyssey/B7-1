import logging
import smtplib

import pytest
from pydantic import SecretStr

from app.config import settings
from app.services.mailer import send_verification_code


class FakeSMTP:
    instances = []
    fail = False

    def __init__(self, host, port, timeout):
        self.args = (host, port, timeout)
        self.calls = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.calls.append("starttls")

    def login(self, username, password):
        self.calls.append(("login", username, password))

    def send_message(self, message):
        if FakeSMTP.fail:
            raise smtplib.SMTPRecipientsRefused({})
        self.calls.append(("send", message))


@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.instances = []
    FakeSMTP.fail = False
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(settings, "smtp_host", "email-smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "user")
    monkeypatch.setattr(settings, "smtp_password", SecretStr("secret"))
    monkeypatch.setattr(settings, "mail_from", "AI 챗봇 <no-reply@example.com>")
    return FakeSMTP


def test_skip_without_smtp_host(monkeypatch, caplog):
    monkeypatch.setattr(settings, "smtp_host", None)
    caplog.set_level(logging.WARNING, logger="app")

    send_verification_code("alice@example.com", "123456")
    assert "mail_skipped to_domain=example.com" in caplog.messages


def test_send_code(smtp, caplog):
    caplog.set_level(logging.INFO, logger="app")

    send_verification_code("alice@example.com", "123456")

    client = smtp.instances[0]
    assert client.args == ("email-smtp.example.com", 587, 10)
    assert client.calls[0] == "starttls"
    assert client.calls[1] == ("login", "user", "secret")
    message = client.calls[2][1]
    assert message["To"] == "alice@example.com"
    assert "123456" in message.get_content()
    assert "mail_sent to_domain=example.com" in caplog.messages


def test_send_fail_logged(smtp, caplog):
    smtp.fail = True
    caplog.set_level(logging.ERROR, logger="app")

    send_verification_code("alice@example.com", "123456")
    assert "mail_send_fail to_domain=example.com error=SMTPRecipientsRefused" in caplog.messages
    assert all("alice@" not in m for m in caplog.messages)
