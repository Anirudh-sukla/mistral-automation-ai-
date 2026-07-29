"""
Simple SMTP email client helper.
Uses environment variables for SMTP configuration.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
import logging

logger = logging.getLogger("email_client")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


def send_email(subject: str, body: str, to: str) -> None:
    if not SMTP_HOST or not SMTP_USER:
        raise RuntimeError("SMTP not configured. Set SMTP_HOST and SMTP_USER in environment.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg.set_content(body)

    context = ssl.create_default_context()
    try:
        # Try TLS on the standard port
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        logger.info("Email sent to %s", to)
    except Exception:
        logger.exception("Failed to send email to %s", to)
        raise
