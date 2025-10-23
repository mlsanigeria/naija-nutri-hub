import os
from pathlib import Path
from azure.communication.email import EmailClient
from dotenv import load_dotenv

load_dotenv()

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_EMAIL_CONNECTION_STRING = os.getenv('ADMIN_EMAIL_CONNECTION_STRING')

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
    # Validate required environment variables
    if not ADMIN_EMAIL or not ADMIN_EMAIL_CONNECTION_STRING:
        return {
            "success": False,
            "message": "Email configuration missing. Please set ADMIN_EMAIL and ADMIN_EMAIL_CONNECTION_STRING in environment variables."
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

        # Send email using Azure Communication Email
        client = EmailClient.from_connection_string(ADMIN_EMAIL_CONNECTION_STRING)
        
        # Create email message
        message = {
            "senderAddress": ADMIN_EMAIL,
            "recipients": {
                "to": [{"address": receiver_email}]
            },
            "content": {
                "subject": "Your Verification Code - Naija Nutri Hub",
                "html": html_content,
                "plainText": f"Your OTP code is: {otp_code}. It expires in {expiry_minutes} minutes."
            },   
        }

        poller = client.begin_send(message)
        result = poller.result()
        # print(result)
        status = result["status"]
        if status != "Succeeded":
            return {"success": False, "message": f"Failed to send OTP email. Status: {status}"}

        return {"success": True, "message": f"OTP sent successfully to {receiver_email}"}

    except FileNotFoundError:
        return {"success": False, "message": "Email template not found"}
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

    subject = "Welcome to Naija Nutri Hub!"
    body = {
        "user_name": user_name,
        "app_name": "Naija Nutri Hub",
        "dashboard_url": "https://naijanutri.com/",
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
        # Send email using Azure Communication Email
        client = EmailClient.from_connection_string(ADMIN_EMAIL_CONNECTION_STRING)
        
        # Create email message
        message = {
            "senderAddress": ADMIN_EMAIL,
            "recipients": {
                "to": [{"address": receiver}]
            },
            "content": {
                "subject": subject,
                "html": html_content,
                "plainText": "Welcome to Naija Nutri Hub!"
            },   
        }

        poller = client.begin_send(message)
        result = poller.result()
        status = result["status"]
        if status != "Succeeded":
            return {"success": False, "message": f"Failed to send Welcome email. Status: {status}"}

        return {"status": "success", "message": f"Welcome email sent to {receiver}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

    
