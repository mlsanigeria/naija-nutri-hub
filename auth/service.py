from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password
import random
import string

def user_serializer(user: dict):
    """
    Extract firstname, lastname, email and username from user create model
    """
  
    return

def get_user_via_email(email: str):
    return


def get_user_via_username(username: str):
    return

def user_exists_email(email: str):
    return


def user_exists_username(username: str):
    return


def create_user(user: UserCreate):
    return

# length of 4 or 6
def generate_otp(length: int = 4) -> str:
    """Generate a random numeric OTP of given length."""
    return
