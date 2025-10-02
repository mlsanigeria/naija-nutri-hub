from config.database import user_auth,otp_record
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password
import random
import string
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from .mail import send_email_otp


def user_serializer(user: dict):
    """
    Extract details from user create model (withough default document id by MongoDB)
    """
  
    return

def get_user_via_email(email: str):
    return user_serializer(...)


def get_user_via_username(username: str):
    return user_serializer(...)

def user_exists_email(email: str) -> bool:
    """
    Check if a user with the given email already exists in the user_auth collection.
    
    :param email: The email address to check.
    :return: True if the user exists, False otherwise.
    """
    # Use count_documents() for an efficient check on the database.
    return user_auth.count_documents({"email": email}) > 0


def user_exists_username(username: str) -> bool:
    """
    Check if a user with the given username already exists in the user_auth collection.
    
    :param username: The username to check.
    :return: True if the user exists, False otherwise.
    """
    # Use count_documents() for an efficient check on the database.
    return user_auth.count_documents({"username": username}) > 0


def create_user(user: UserCreate):
    return

# length of 6
def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of given length."""
    return

def resend_otp_service(email: str):
    now = datetime.now(timezone.utc)

    user = user_auth.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    last_otp = otp_record.find_one({"email": email}, sort=[("created_at", -1)])
    if last_otp:
        created_at = last_otp["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if (now - created_at) < timedelta(seconds=60):
            raise HTTPException(status_code=429, detail="Please wait before requesting another OTP")

    otp_record.delete_many({"email": email})

    otp_code = str(random.randint(100000, 999999))
    otp_data = {
        "email": email,
        "otp": otp_code,
        "created_at": now,
        "expires_at": now + timedelta(minutes=5),
        "is_used": False
    }
    otp_record.insert_one(otp_data)

    send_email_otp(
        subject="Your OTP Code",
        body=f"Your OTP is {otp_code}. It will expire in 5 minutes.",
        receiver=email
    )

    return {"message": "OTP resent successfully", "email": email}
