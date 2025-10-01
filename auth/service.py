from config.database import user_auth
from schemas.schema import User, UserCreate
from datetime import datetime
from .utils import hash_password
import random
import string
from bson import ObjectId
from fastapi import HTTPException

def user_serializer(user: dict) -> dict:
    """
    Extract details from user create model (without default document id by MongoDB)
    
    Args:
        user (dict): User document from MongoDB
        
    Returns:
        dict: User data without MongoDB ObjectId
    """
    if not user:
        return None
    
    # Convert ObjectId to string for JSON serialization
    user["_id"] = str(user["_id"])
    return user

def get_user_via_email(email: str) -> dict:
    """
    Get user by email address
    
    Args:
        email (str): User's email address
        
    Returns:
        dict: User data or None if not found
    """
    user = user_auth.find_one({"email": email})
    return user_serializer(user)

def get_user_via_username(username: str) -> dict:
    """
    Get user by username
    
    Args:
        username (str): User's username
        
    Returns:
        dict: User data or None if not found
    """
    user = user_auth.find_one({"username": username})
    return user_serializer(user)

def user_exists_email(email: str) -> bool:
    """
    Check if user exists with given email
    
    Args:
        email (str): Email to check
        
    Returns:
        bool: True if user exists, False otherwise
    """
    return user_auth.find_one({"email": email}) is not None

def user_exists_username(username: str) -> bool:
    """
    Check if user exists with given username
    
    Args:
        username (str): Username to check
        
    Returns:
        bool: True if user exists, False otherwise
    """
    return user_auth.find_one({"username": username}) is not None

def create_user(user: UserCreate) -> dict:
    """
    Create a new user in the database
    
    Args:
        user (UserCreate): User data from request
        
    Returns:
        dict: Created user data
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Check if user already exists
    if user_exists_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    if user_exists_username(user.username):
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Hash the password
    hashed_password = hash_password(user.password)
    
    # Create user document
    current_time = datetime.utcnow()
    user_doc = {
        "firstname": user.firstname,
        "lastname": user.lastname,
        "username": user.username,
        "email": user.email,
        "password_hash": hashed_password,
        "is_verified": False,
        "created_at": current_time,
        "updated_at": current_time,
        "last_used": current_time,
        "referral_code": user.referral_code
    }
    
    try:
        # Insert user into database
        result = user_auth.insert_one(user_doc)
        
        # Get the created user
        created_user = user_auth.find_one({"_id": result.inserted_id})
        
        # Return serialized user data (without password hash)
        user_data = user_serializer(created_user)
        if user_data:
            # Remove password hash from response
            user_data.pop("password_hash", None)
        
        return user_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )

def generate_otp(length: int = 4) -> str:
    """
    Generate a random numeric OTP of given length
    
    Args:
        length (int): Length of OTP (default: 4)
        
    Returns:
        str: Generated OTP
    """
    return ''.join(random.choices(string.digits, k=length))
