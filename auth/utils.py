from passlib.context import CryptContext
import pytz
import logging
from datetime import datetime


UTC = pytz.UTC
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

otp_context = pwd_context


def hash_password(password: str) -> str:
    """
    Hash a password for storing.
    """
    logger.info('Generating Password Hash.')
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a plain password against the stored hash.
    """
    logger.info('Verifying Password.')
    return pwd_context.verify(password, hashed)


def hash_otp(otp: str) -> str:
    """
    Hash OTP before storing in DB.
    We use the same CryptContext for simplicity.
    """
    logger.info('Hashing OTP.')
    return otp_context.hash(otp)


def verify_otp(otp: str, hashed: str) -> bool:
    """
    Verify an OTP against the hashed version.
    """
    logger.info('Verifying OTP.')
    try:
        return otp_context.verify(otp, hashed)
    except Exception:
        logger.info('OTP Verification Failed.')
        return False


def _now_utc():
    return datetime.utcnow().replace(tzinfo=UTC)
