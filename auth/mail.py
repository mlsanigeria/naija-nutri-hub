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

def send_email_welcome(subject, body, receiver, attachment=False):
    # Create a secure SSL context
    msg = EmailMessage()

    # ...
    return
    
