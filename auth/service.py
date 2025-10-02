from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password

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
    return user

def get_user_via_username(username: str):
    """Fetches a user from the database by their username."""
    user = user_auth.find_one({"username": username})
    return user

def user_exists_email(email: str) -> bool:
    """Checks if a user with the given email already exists."""
    return user_auth.count_documents({"email": email}) > 0

def user_exists_username(username: str) -> bool:
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
        "is_verified": False, # Or True if not implementing OTP for now
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_used": datetime.utcnow(),
    }
    result = user_auth.insert_one(user_data)
    created_user = user_auth.find_one({"_id": result.inserted_id})
    return user_serializer(created_user)

# This can be expanded later
def generate_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of a given length."""
    import random
    import string
    return "".join(random.choices(string.digits, k=length))
