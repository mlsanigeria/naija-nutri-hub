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

def send_email_otp(receiver_email, otp_code, expiry_minutes=10, user_name="User"):
    """
    Send OTP email to user using the otp_request.html template.

    Args:
        receiver_email: Email address to send OTP to
        otp_code: The OTP code to send
        expiry_minutes: How long the OTP is valid (default: 10 minutes)
        user_name: User's display name (default: "User")

    Returns:
        dict: Success/failure message
    """
    # Skip real email sending during tests
    if os.getenv("ENVIRONMENT") == "test":
        return {
            "success": True,
            "message": f"[TEST MODE] OTP simulated for {receiver_email}"
        }
        
    # Validate required environment variables
    if not ADMIN_EMAIL or not ADMIN_EMAIL_PASSWORD or not SERVER:
        return {
            "success": False,
            "message": "Email configuration missing. Please set ADMIN_EMAIL, ADMIN_EMAIL_PASSWORD, and SERVER in environment variables."
        }

    try:
        # Load the HTML template
        template_path = Path(__file__).parent / 'html_email_themes' / 'otp_request.html'
        with open(template_path, 'r') as f:
            html_content = f.read()

        # Replace placeholders in template
        html_content = html_content.replace('{{otp}}', str(otp_code))
        html_content = html_content.replace('{{expiry_minutes}}', str(expiry_minutes))
        html_content = html_content.replace('{{user_name}}', user_name)
        html_content = html_content.replace('{{app_name}}', 'Naija Nutri Hub')
        html_content = html_content.replace('{{support_email}}', ADMIN_EMAIL or 'support@naijanutri.com')

        # Create email message
        msg = EmailMessage()
        msg['Subject'] = 'Your Verification Code - Naija Nutri Hub'
        msg['From'] = ADMIN_EMAIL
        msg['To'] = receiver_email
        msg.set_content('Your OTP code is: ' + str(otp_code))  # Plain text fallback
        msg.add_alternative(html_content, subtype='html')  # HTML version

        # Send email via SMTP with SSL
        with smtplib.SMTP_SSL(SERVER, 465, context=context) as smtp:
            smtp.login(ADMIN_EMAIL, ADMIN_EMAIL_PASSWORD)
            smtp.send_message(msg)

        return {"success": True, "message": f"OTP sent successfully to {receiver_email}"}

    except FileNotFoundError:
        return {"success": False, "message": "Email template not found"}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"Failed to send email: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error sending OTP: {str(e)}"}

def send_email_welcome(user_name, receiver, attachment=False):
    """
    Sends a Welcome Email to the user after successful registration.
    Uses the HTML template from auth/html_email_themes/welcome.html
    
    Args:
        user_name (str): The name of the user to personalize the email.
        receiver (str): The email address of the recipient.
        attachment (str or bool): Path to a file to attach, or False for no attachment.
    """
    # Skip real email sending during tests
    if os.getenv("ENVIRONMENT") == "test":
        return {"status": "success", "message": f"[TEST MODE] Welcome email simulated for {receiver}"}
        
    subject = "Welcome to Naija Nutri Hub!"
    body = {
        "user_name": user_name,
        "app_name": "Naija Nutri Hub",
        "dashboard_url": "https://naijanutri.com/dashboard",
        "support_email": ADMIN_EMAIL
    }
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

    
