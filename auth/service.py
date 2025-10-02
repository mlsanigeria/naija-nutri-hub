from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password
import random
import string
from bson import ObjectId # <-- Added for database interaction

def user_serializer(user: dict):
    """
    Extract details from user create model (withough default document id by MongoDB)
    """
    # This function needs implementation for the getters to work correctly
    return

def get_user_via_email(email: str):
    return user_serializer(...)


def get_user_via_username(username: str):
    return user_serializer(...)

def user_exists_email(email: str) -> bool:
    """
    Checks if a user with the given email address already exists (case-insensitive).
    """
    try:
        # Check for user by email, forcing lowercase for case-insensitivity.
        # Project {"_id": 1} for efficiency (only need to check if a document exists).
        user = user_auth.find_one({"email": email.lower()}, {"_id": 1}) 
        return user is not None
    except Exception as e:
        print(f"Database error during user_exists_email check: {e}")
        return False


def user_exists_username(username: str) -> bool:
    """
    Checks if a user with the given username already exists (case-sensitive by default in MongoDB).
    """
    try:
        # Check for user by exact username.
        # Project {"_id": 1} for efficiency.
        user = user_auth.find_one({"username": username}, {"_id": 1})
        return user is not None
    except Exception as e:
        print(f"Database error during user_exists_username check: {e}")
        return False


def create_user(user: UserCreate):
    return

# length of 6
def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of given length."""
    return