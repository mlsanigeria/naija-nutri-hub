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
    Extract details from user create model (withough default document id by MongoDB)
    """
  
    return

def get_user_via_email(email: str):
    return user_serializer(...)


def get_user_via_username(username: str):
    return user_serializer(...)

def user_exists_email(email: str) -> bool:
    return


def user_exists_username(username: str) -> bool:
    return


def create_user(user: UserCreate):
    return

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
    """
    logger.info('Resending OTP...')
    user_doc = user_auth.find_one({"email": email})
    if not user_doc:
        logger.error("User not found")
        return {"ok": False, "message": "User not found"}

    if user_doc.get("is_verified"):
        logger.error("Account already verified")
        return {"ok": False, "message": "Account already verified"}

    now = u._now_utc()
    last_sent = user_doc.get("otp_last_sent")
    resend_count = user_doc.get("otp_resend_count", 0)
    resend_window_start = user_doc.get("otp_resend_window_start")

    # Normalize datetimes if stored as strings
    def _normalize(dt):
        if not dt:
            return None
        if isinstance(dt, str):
            try:
                return datetime.fromisoformat(dt).replace(tzinfo=u.UTC)
            except Exception:
                return None
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=u.UTC)
            return dt
        return None

    last_sent = _normalize(last_sent)
    resend_window_start = _normalize(resend_window_start)

    # Enforce minimal interval between resends
    if last_sent and (now - last_sent).total_seconds() < MIN_RESEND_INTERVAL_SECONDS:
        logger.error(f"Please wait before requesting a new OTP (min {MIN_RESEND_INTERVAL_SECONDS}s between requests).")
        return {"ok": False, "message": f"Please wait before requesting a new OTP (min {MIN_RESEND_INTERVAL_SECONDS}s between requests)."}

    # Reset window if necessary
    if not resend_window_start or (now - resend_window_start).total_seconds() > RESEND_WINDOW_SECONDS:
        resend_window_start = now
        resend_count = 0

    if resend_count >= MAX_RESENDS_PER_WINDOW:
        logger.error("Too many OTP requests. Please try again later.")
        return {"ok": False, "message": "Too many OTP requests. Please try again later."}

    # Generate new OTP
    otp_plain = generate_otp()
    otp_hashed = u.hash_otp(otp_plain)
    otp_expires_at = now + timedelta(minutes=OTP_TTL_MINUTES)

    # Update DB: overwrite otp fields, increment resend_count, update timestamps
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

    # send email
    subject = "Your new verification code"
    body = f"Your new OTP code is: {otp_plain}\nIt will expire in {OTP_TTL_MINUTES} minutes."
    sent = m.send_email_otp(subject, body, email)
    if not sent:
        logger.error("Failed to send OTP email. Please try again later.")
        return {"ok": False, "message": "Failed to send OTP email. Please try again later."}

    return {"ok": True, "message": "A new OTP has been sent to your email."}
