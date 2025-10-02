import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_EMAIL_PASSWORD = os.getenv('ADMIN_EMAIL_PASSWORD')
SERVER = os.getenv('SERVER')

context = ssl._create_unverified_context()


def _parse_server(server: str):
    """Return (host, port) tuple from SERVER env var."""
    if ":" in server:
        host, port_str = server.split(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 465
    else:
        host = server
        port = 465
    return host, port

def send_email_otp(subject: str, body: str, receiver: str, attachment: Optional[Path] = None) -> bool:
    """
    Send an email (used to deliver OTPs).

    Returns True on success, False on failure.
    """
    if not ADMIN_EMAIL or not ADMIN_EMAIL_PASSWORD:
        logger.info("ADMIN_EMAIL or ADMIN_EMAIL_PASSWORD not set")
        return False

    host, port = _parse_server(SERVER)

    # Create a secure SSL context
    msg = EmailMessage()
    msg["From"] = ADMIN_EMAIL
    msg["To"] = receiver
    msg["Subject"] = subject
    msg.set_content(body)
    html_body = f"<html><body><pre style='font-family: monospace;'>{body}</pre></body></html>"
    msg.add_alternative(html_body, subtype="html")

    # Attach file if provided
    if attachment and attachment.exists():
        try:
            with open(attachment, "rb") as f:
                data = f.read()
                maintype = "application"
                subtype = "octet-stream"
                msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=attachment.name)
        except Exception as e:
            logger.error(f"Failed to attach file: {e}")

    try:
        # Using SMTP_SSL for secure connection
        with smtplib.SMTP_SSL(host=host, port=port, context=context) as server:
            server.login(ADMIN_EMAIL, ADMIN_EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
