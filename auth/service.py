from config.database import user_auth
from schemas.schema import User, UserCreate # Assuming User is the database model/schema
from datetime import datetime
from .utils import hash_password
import random
import string
from bson import ObjectId # Import ObjectId for querying by ID if needed

def user_serializer(user: dict) -> dict:
    """
    Extract details from a MongoDB user document and format it.
    
    Args:
        user: The raw user dictionary retrieved from MongoDB.
        
    Returns:
        A dictionary representation suitable for the application.
    """
    # Convert MongoDB's ObjectId to a string for JSON compatibility
    return {
        "id": str(user.get("_id")),
        "username": user.get("username"),
        "email": user.get("email"),
        "is_verified": user.get("is_verified", False),
        "created_at": user.get("created_at")
        # Include other fields as necessary, but exclude the password hash
    }

def get_user_via_email(email: str) -> dict | None:
    """
    Retrieves a user document from the database by email.
    """
    user = user_auth.find_one({"email": email.lower()})
    if user:
        return user_serializer(user)
    return None


def get_user_via_username(username: str) -> dict | None:
    """
    Retrieves a user document from the database by username.
    """
    user = user_auth.find_one({"username": username})
    if user:
        return user_serializer(user)
    return None

def user_exists_email(email: str) -> bool:
    """
    Checks if a user with the given email address already exists.
    """
    try:
        # Check for user, storing and checking emails in lowercase for case-insensitivity
        user = user_auth.find_one({"email": email.lower()}, {"_id": 1}) 
        return user is not None
    except Exception as e:
        print(f"Database error during user_exists_email check: {e}")
        return False


def user_exists_username(username: str) -> bool:
    """
    Checks if a user with the given username already exists.
    """
    try:
        # Check for user
        user = user_auth.find_one({"username": username}, {"_id": 1})
        return user is not None
    except Exception as e:
        print(f"Database error during user_exists_username check: {e}")
        return False


def create_user(user_data: dict) -> object:
    """
    Saves a new user document to the database.
    
    Args:
        user_data: A dictionary containing the user's data (with hashed password).
        
    Returns:
        The result object from the MongoDB insert operation.
    """
    # Ensure standard fields are set
    if "is_verified" not in user_data:
        user_data["is_verified"] = False
    
    user_data["created_at"] = datetime.now()
    user_data["email"] = user_data["email"].lower() # Force lowercase for emails
    
    result = user_auth.insert_one(user_data)
    return result

def generate_otp(length: int = 4) -> str:
    """Generate a random numeric OTP of given length (4 or 6)."""
    if length not in [4, 6]:
        length = 4 # Default to 4 if an invalid length is passed
        
    # Generate a string of 'length' random digits
    return ''.join(random.choices(string.digits, k=length))