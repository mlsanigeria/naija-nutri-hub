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
