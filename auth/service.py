from config.database import user_auth, otp_record
from schemas.schema import User, UserCreate
from datetime import datetime, timedelta, timezone
from .utils import hash_password
from fastapi import HTTPException
from .mail import send_email_otp
import random
import string
import uuid


def user_serializer(user: dict) -> dict:
    """
    Serializes a user document from MongoDB into a dictionary,
    converting the '_id' to a string.
    """
    if not user:
        return None
    return {
        "id": str(user["_id"]),
        "firstname": user["firstname"],
        "lastname": user["lastname"],
        "username": user["username"],
        "email": user["email"],
        "is_verified": user["is_verified"],
        "created_at": user["created_at"],
    }


def get_user_via_email(email: str):
    """Fetches a user from the database by their email."""
    user = user_auth.find_one({"email": email})
    return user_serializer(user)


def get_user_via_username(username: str):
    """Fetches a user from the database by their username."""
    user = user_auth.find_one({"username": username})
    return user_serializer(user)


def user_exists_email(email: str) -> bool:
    """
    Check if a user with the given email already exists in the user_auth collection.
    
    :param email: The email address to check.
    :return: True if the user exists, False otherwise.
    """
    # Use count_documents() for an efficient check on the database.
    return user_auth.count_documents({"email": email}) > 0
    """Checks if a user with the given email already exists."""
    return user_auth.count_documents({"email": email}) > 0


def user_exists_username(username: str) -> bool:
    """
    Check if a user with the given username already exists in the user_auth collection.
    
    :param username: The username to check.
    :return: True if the user exists, False otherwise.
    """
    # Use count_documents() for an efficient check on the database.
    return user_auth.count_documents({"username": username}) > 0
    """Checks if a user with the given username already exists."""
    return user_auth.count_documents({"username": username}) > 0


def create_user(user: UserCreate):
    """Creates a new user in the database."""
    hashed_pass = hash_password(user.password)
    user_data = {
        "firstname": user.firstname,
        "lastname": user.lastname,
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_pass,
        "is_verified": False,  # Or True if not implementing OTP for now
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_used": datetime.utcnow(),
    }
    result = user_auth.insert_one(user_data)
    created_user = user_auth.find_one({"_id": result.inserted_id})
    return user_serializer(created_user)


def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of a given length."""
    return "".join(random.choices(string.digits, k=length))


def resend_otp_service(email: str):
    """
    Resend OTP to a user with rate limiting.
    Ensures no OTP is resent within 60 seconds of the last request.
    """
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

def generate_reset_token() -> str:
    """Generate a secure, random token using UUID4."""
    return str(uuid.uuid4())

def request_password_reset(email: str):
    """
    Generates a password reset token, saves it, and sends it via email.
    """
    user = user_auth.find_one({"email": email}) 
    if not user:
        # Security: return success even if the email isn't found
        return {"message": "If an account with that email exists, a password reset link has been sent."}

    now = datetime.now(timezone.utc)
    
    # Rate limiting (5 minutes)
    last_reset_request = otp_record.find_one(
        {"email": email, "type": "PASSWORD_RESET"},
        sort=[("created_at", -1)]
    )
    if last_reset_request:
        created_at = last_reset_request["created_at"]
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if (now - created_at) < timedelta(minutes=5): 
             return {"message": "If an account with that email exists, a password reset link has been sent."}


    # Invalidate any existing, unused reset tokens for this user
    otp_record.update_many(
        {"email": email, "is_used": False, "type": "PASSWORD_RESET"},
        {"$set": {"is_used": True}}
    )

    # Generate Token and Expiry (1 hour)
    reset_token = generate_reset_token()
    token_expiry = now + timedelta(hours=1) 

    # Save the token record
    reset_data = {
        "email": email,
        "token": reset_token, # Use 'token' field for UUID
        "type": "PASSWORD_RESET", # New field to distinguish
        "created_at": now,
        "expires_at": token_expiry,
        "is_used": False
    }
    otp_record.insert_one(reset_data)

    # Send the email
    reset_link = f"http://yourfrontend.com/reset-password?token={reset_token}" # Adjust the frontend link
    send_email_otp(
        subject="Password Reset Request",
        body=f"You requested a password reset. Use the following link to set a new password. The link expires in 1 hour: {reset_link}",
        receiver=email
    )

    return {"message": "If an account with that email exists, a password reset link has been sent."}


def reset_user_password(token: str, new_password: str):
    """
    Verifies the reset token and updates the user's password.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Find the token record (using 'token' field and 'PASSWORD_RESET' type)
    token_record = otp_record.find_one({
        "token": token, 
        "type": "PASSWORD_RESET"
    })

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")
    
    # 2. Check token status and expiry
    if token_record["is_used"]:
        raise HTTPException(status_code=400, detail="Token already used.")

    expires_at = token_record["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
        
    if now > expires_at:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")

    # 3. Find the user
    email = token_record["email"]
    user = user_auth.find_one({"email": email})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 4. Hash the new password and update the user document
    hashed_pass = hash_password(new_password)
    user_auth.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hashed_pass, 
                "updated_at": datetime.utcnow()
            }
        }
    )

    # 5. Invalidate the token
    otp_record.update_one(
        {"_id": token_record["_id"]},
        {"$set": {"is_used": True}}
    )

    # 6. Return success
    return {"message": "Password successfully reset."}