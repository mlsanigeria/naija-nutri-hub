import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_EMAIL_PASSWORD = os.getenv('ADMIN_EMAIL_PASSWORD')
SERVER = os.getenv('SERVER')

context = ssl._create_unverified_context()    

def send_email_otp(subject, body, receiver, attachment=False):
    # Create a secure SSL context
    msg = EmailMessage()

    # ...
    return

def send_email_welcome(subject, body, receiver, attachment=False):
    """
    Sends a Welcome Email to the user after successful registration.
    Uses the HTML template from auth/html_email_themes/welcome.html
    """
    try:
        # --- Load HTML Template ---
        template_path = Path(__file__).parent / "html_email_themes" / "onboarding.html"
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # Replace placeholders with actual values
        html_content = (
            html_template
            .replace("{{user_name}}", body.get("user_name", "User"))
            .replace("{{app_name}}", body.get("app_name", "Naija Nutri Hub"))
            .replace("{{dashboard_url}}", body.get("dashboard_url", "#"))
            .replace("{{support_email}}", body.get("support_email", ADMIN_EMAIL))
        )

        # --- Prepare Email Message ---
        msg = EmailMessage()
        msg["From"] = ADMIN_EMAIL
        msg["To"] = receiver
        msg["Subject"] = subject
        msg.set_content("Welcome to Naija Nutri Hub!")  # Plain text fallback
        msg.add_alternative(html_content, subtype="html")

        # Optional attachment
        if attachment:
            with open(attachment, "rb") as f:
                file_data = f.read()
                file_name = os.path.basename(attachment)
            msg.add_attachment(
                file_data, maintype="application", subtype="octet-stream", filename=file_name
            )

        # --- Send Email ---
        with smtplib.SMTP_SSL(SERVER, 465, context=context) as smtp:
            smtp.login(ADMIN_EMAIL, ADMIN_EMAIL_PASSWORD)
            smtp.send_message(msg)

        return {"status": "success", "message": f"Welcome email sent to {receiver}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    
