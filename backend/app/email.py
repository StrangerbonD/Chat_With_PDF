import logging
from email.mime.text import MIMEText
import aiosmtplib
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    """
    Send an email via Brevo HTTPS API, Resend HTTPS API, or SMTP (STARTTLS).
    If no credentials are provided, logs to stdout via the Dev Email Simulator.
    """
    s = get_settings()

    # 1. Brevo HTTP API (Recommended for Render Free tier, port 443 HTTPS)
    if s.brevo_api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.brevo.com/v3/smtp/email",
                    headers={
                        "api-key": s.brevo_api_key,
                        "content-type": "application/json",
                    },
                    json={
                        "sender": {"email": s.smtp_from, "name": "Chat with PDF"},
                        "to": [{"email": to}],
                        "subject": subject,
                        "textContent": body,
                    },
                )
                if res.status_code in (200, 201, 202):
                    logger.info("Email delivered to %s via Brevo API", to)
                    return
                logger.error("Brevo API error (%d): %s", res.status_code, res.text)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email via Brevo API to %s: %s", to, exc)
        return

    # 2. Resend HTTP API (Port 443 HTTPS)
    if s.resend_api_key:
        try:
            from_addr = s.smtp_from if (s.smtp_from and "@resend.dev" in s.smtp_from) else "onboarding@resend.dev"
            payload = {
                "from": f"Bondhon Das <{from_addr}>",
                "to": [to],
                "subject": subject,
                "text": body,
                "reply_to": "bondhondas16@gmail.com",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {s.resend_api_key}",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
                if res.status_code in (200, 201):
                    logger.info("Email delivered to %s via Resend API", to)
                    return
                logger.error("Resend API error (%d): %s", res.status_code, res.text)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email via Resend API to %s: %s", to, exc)
        return

    # 3. Standard SMTP (Works on VPS or paid compute where 587 is unblocked)
    if s.smtp_user and s.smtp_password:
        from_email = s.smtp_from or "bondhondas16@gmail.com"
        message = MIMEText(body, "plain", "utf-8")
        message["From"] = f"Bondhon Das <{from_email}>"
        message["Reply-To"] = "bondhondas16@gmail.com"
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
            logger.info("Email delivered to %s via SMTP", to)
            return
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email via SMTP to %s: %s", to, exc)
        return

    # 4. Fallback: Log locally for testing without setup
    logger.info(
        "=== [DEV EMAIL SIMULATOR] ===\nTo: %s\nSubject: %s\nBody:\n%s\n=============================",
        to,
        subject,
        body,
    )
