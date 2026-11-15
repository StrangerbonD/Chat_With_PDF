import logging
from email.mime.text import MIMEText
import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via STARTTLS SMTP.
    If SMTP credentials are not configured, logs the email content (including OTP)
    so development and testing work seamlessly without hanging.
    """
    s = get_settings()

    # If no SMTP credentials provided, log the code locally and return immediately
    if not s.smtp_user or not s.smtp_password:
        logger.info(
            "=== [DEV EMAIL SIMULATOR] ===\nTo: %s\nSubject: %s\nBody:\n%s\n=============================",
            to,
            subject,
            body,
        )
        return

    message = MIMEText(body, "plain", "utf-8")
    message["From"] = s.smtp_from
    message["To"] = to
    message["Subject"] = subject

    try:
        await aiosmtplib.send(
            message,
            hostname=s.smtp_host,
            port=s.smtp_port,
            username=s.smtp_user,
            password=s.smtp_password,
            start_tls=True,
            timeout=5,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email to %s: %s", to, exc)
