from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime, timedelta
import utils as u
import mail as m
import random
import string
import logging

logger = logging.getLogger(__name__)

# Configuration constants
OTP_LENGTH = 6
OTP_TTL_MINUTES = 10
MIN_RESEND_INTERVAL_SECONDS = 30
RESEND_WINDOW_SECONDS = 3600  # 1 hour window
MAX_RESENDS_PER_WINDOW = 5


def user_serializer(user: dict):
    """
    Extract public details from a MongoDB user document.
    """
    if not user:
        return None
    return {
        "id": str(user.get("_id")),
        "email": user.get("email"),
        "username": user.get("username"),
        "is_verified": user.get("is_verified", False),
    }


def get_user_via_email(email: str):
    doc = user_auth.find_one({"email": email})
    return user_serializer(doc)


def user_exists_username(username: str) -> bool:
    return user_auth.count_documents({"username": username}) > 0


def user_exists_email(email: str) -> bool:
    return user_auth.count_documents({"email": email}) > 0


def user_exists_username(username: str) -> bool:
    return user_auth.count_documents({"username": username}) > 0


def create_user(user: UserCreate):
    """
    Create a new user document, store hashed password,
    generate OTP, send email and return serializer.
    `user` is expected to be an object or dict with 'email', 'username', 'password' attrs.
    """
    email = getattr(user, "email", None) or user.get("email")
    username = getattr(user, "username", None) or user.get("username")
    password = getattr(user, "password", None) or user.get("password")

    if user_exists_email(email):
        raise ValueError("Email already exists")

    if user_exists_username(username):
        raise ValueError("Username already exists")

    hashed_pw = u.hash_password(password)

    otp_plain = generate_otp()
    otp_hashed = u.hash_otp(otp_plain)
    now = u._now_utc()
    otp_expires_at = now + timedelta(minutes=OTP_TTL_MINUTES)

    doc = {
        "email": email,
        "username": username,
        "password": hashed_pw,
        "is_verified": False,
        "otp_hash": otp_hashed,
        "otp_expires_at": otp_expires_at,
        "otp_last_sent": now,
        "otp_resend_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    res = user_auth.insert_one(doc)
    # send email
    subject = "Your verification code"
    body = f"Your OTP code is: {otp_plain}\nIt will expire in {OTP_TTL_MINUTES} minutes."
    m.send_email_otp(subject, body, email)

    # return created user (sanitized)
    created = user_auth.find_one({"_id": res.inserted_id})
    return user_serializer(created)


# length of 4 or 6
def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a random numeric OTP of given length."""
    # Use digits only for simplicity
    digits = string.digits
    return "".join(random.choice(digits) for _ in range(length))


def resend_otp(email: str) -> dict:
    """
    Generate & send a fresh OTP to the user's email.
    Enforce rate limits to prevent abuse.
    Intended for use in /resend_otp API endpoint.
    """
    logger.info(f"Resend OTP request for {email}")
    user_doc = user_auth.find_one({"email": email})
    if not user_doc:
        logger.warning(f"Resend OTP failed: user {email} not found")
        return {"ok": False, "message": "User not found"}

    if user_doc.get("is_verified"):
        logger.warning(f"Resend OTP failed: {email} already verified")
        return {"ok": False, "message": "Account already verified"}

    now = u._now_utc()
    last_sent = user_doc.get("otp_last_sent")
    resend_count = user_doc.get("otp_resend_count", 0)
    resend_window_start = user_doc.get("otp_resend_window_start")

    # Normalize datetime fields
    def _normalize(dt):
        if not dt:
            return None
        if isinstance(dt, str):
            try:
                return datetime.fromisoformat(dt).replace(tzinfo=u.UTC)
            except Exception:
                return None
        if isinstance(dt, datetime):
            return dt if dt.tzinfo else dt.replace(tzinfo=u.UTC)
        return None

    last_sent = _normalize(last_sent)
    resend_window_start = _normalize(resend_window_start)

    # Enforce minimal interval between requests
    if last_sent and (now - last_sent).total_seconds() < MIN_RESEND_INTERVAL_SECONDS:
        wait_time = MIN_RESEND_INTERVAL_SECONDS - int((now - last_sent).total_seconds())
        logger.info(f"Resend OTP throttled for {email}, must wait {wait_time}s")
        return {"ok": False, "message": f"Please wait {wait_time} seconds before requesting a new OTP."}

    # Reset rate-limit window if expired
    if not resend_window_start or (now - resend_window_start).total_seconds() > RESEND_WINDOW_SECONDS:
        resend_window_start = now
        resend_count = 0

    if resend_count >= MAX_RESENDS_PER_WINDOW:
        logger.warning(f"Resend OTP blocked for {email}: too many requests in window")
        return {"ok": False, "message": "Too many OTP requests. Please try again later."}

    # Generate and hash new OTP
    otp_plain = generate_otp()
    otp_hashed = u.hash_otp(otp_plain)
    otp_expires_at = now + timedelta(minutes=OTP_TTL_MINUTES)

    # Update user document
    update_doc = {
        "$set": {
            "otp_hash": otp_hashed,
            "otp_expires_at": otp_expires_at,
            "otp_last_sent": now,
            "otp_resend_window_start": resend_window_start,
            "updated_at": now,
        },
        "$inc": {"otp_resend_count": 1},
    }
    user_auth.update_one({"_id": user_doc["_id"]}, update_doc)

    # Send OTP email
    subject = "Your new verification code"
    body = f"Your new OTP code is: {otp_plain}\nIt will expire in {OTP_TTL_MINUTES} minutes."
    if not m.send_email_otp(subject, body, email):
        logger.error(f"OTP email send failure for {email}")
        return {"ok": False, "message": "Failed to send OTP email. Please try again later."}

    logger.info(f"New OTP sent successfully to {email}")
    return {"ok": True, "message": "A new OTP has been sent to your email."}
