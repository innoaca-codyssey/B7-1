import logging
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.logging_config import log_event


def send_verification_code(to: str, code: str) -> None:
    to_domain = to.rsplit("@", 1)[-1]
    if not settings.smtp_host:
        log_event("mail_skipped", level=logging.WARNING, to_domain=to_domain)
        return

    message = EmailMessage()
    message["Subject"] = "[AI 챗봇] 이메일 인증 코드"
    message["From"] = settings.mail_from
    message["To"] = to
    message.set_content(
        f"인증 코드: {code}\n\n코드는 10분 동안 유효합니다. 회원가입 화면에 코드를 입력해 주세요."
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError) as e:
        log_event(
            "mail_send_fail", level=logging.ERROR, to_domain=to_domain, error=type(e).__name__
        )
        return
    log_event("mail_sent", to_domain=to_domain)
