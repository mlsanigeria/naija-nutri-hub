from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password
import random
import string

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

# length of 6
def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of given length."""
    return
