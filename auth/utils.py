from passlib.context import CryptContext
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
otp_context = pwd_context

def hash_password(password):
    return

def verify_password(password, hashed):
    return

def hash_otp(otp: str) -> str:
    """
    Hash OTP before storing in DB.
    We use the same CryptContext for simplicity.
    """
    logger.info('Hashing OTP.')
    return otp_context.hash(otp)