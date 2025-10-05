import os
import random
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jose import JWTError
from fastapi import FastAPI, Depends, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bson import ObjectId
from auth.service import resend_otp_service

# Food Classification
from src.food_classifier.image_classification import classify_image, get_related_foods

# Authentication
from auth.mail import send_email_otp
from auth.service import (
    create_user,
    generate_otp,
    get_user_via_email,
    get_user_via_username,
    user_exists_email,
    user_exists_username,
    user_serializer,
    resend_otp_service,
)
from auth.utils import hash_password, verify_password

# Schema/Database
from schemas.schema import (
    LoginRequest,
    OTPModel,
    OTPVerifyRequest,
    ResetPasswordRequest,
    UserCreate,
    FoodClassificationResponse,
    ErrorResponse,
)
from config.database import otp_record, user_auth

# Load environment variables
load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token will be valid for 30 minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- Helper Functions for JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decodes token and returns user if valid, otherwise raises exception."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_via_username(username)
    if user is None:
        raise credentials_exception
    return user


app = FastAPI(
    title="Naija Nutri Hub API",
    description="Backend API documentation for the Naija Nutri Hub project",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home
@app.get("/", tags=["Home"])
def index():
    return {"Project": "Naija Nutri Hub"}


# Create new user
@app.post("/sign-up", tags=["Authentication"])
def sign_up_user(user_data: UserCreate):
    """Handles new user registration."""
    if user_exists_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_exists_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = create_user(user_data)
    return {"message": "User created successfully!", "user": new_user}


@app.post("/verify", tags=["Authentication"])
def verify_user_account(otp_data: OTPVerifyRequest):
    """ Verify user account using OTP"""

    # Check the OTP record
    otp_rec = otp_record.find_one({
        "email": otp_data.email,
        "otp": otp_data.otp
    })

    if not otp_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect OTP",
        ) 
    
    # Check for 10 minutes otp expiry 
    otp_age = datetime.now(timezone.utc) - otp_rec["created_at"]
    OTP_EXPIRY_MINUTES = 10
    
    if otp_age > timedelta(minutes=OTP_EXPIRY_MINUTES):
        # Delete expired OTP
        otp_record.delete_one({"email": otp_rec["email"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new one"
        )
    
    # Find user
    user = user_auth.find_one({"email": otp_rec["email"]})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_auth.update_one({"email": user["email"]}, {
        "$set": {
            "is_verified": True,
            "updated_at": datetime.now(timezone.utc)
        }
    })

    otp_record.delete_one({"email": otp_rec["email"]})
    return {"message": "Account verified successfully"}


@app.post("/resend_otp", tags=["Authentication"])
def resend_otp(email: str):
    """Resend OTP using the service function."""
    return resend_otp_service(email)


@app.post("/login", tags=["Authentication"])
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Logs in a user and returns a JWT access token.
    FastAPI's form dependency expects 'username' and 'password' fields.
    """
    # Check if user exists (can be username or email)
    user = get_user_via_username(form_data.username)
    if not user:
        user = get_user_via_email(form_data.username)

    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- Example Protected Route ---
@app.get("/users/me", tags=["Users"])
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    An example protected route that returns the current authenticated user's data.
    """
    # We serialize it here to hide sensitive info like password hash
    return user_serializer(current_user)


@app.post("/verify_reset_otp", tags=["Authentication"])
def verify_reset_otp(otp_data: OTPVerifyRequest):
    """
    Verifies the OTP sent for password reset.
    """
    otp_entry = otp_record.find_one({
        "email": otp_data.email,
        "otp": otp_data.otp
    })

    # If OTP record not found
    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check if OTP is expired (5 minutes validity)
    now = datetime.now(timezone.utc)
    expires_at = otp_entry["created_at"] + timedelta(minutes=5)

    if now > expires_at:
        otp_record.delete_one({"email": otp_data.email})
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one")
    
    # If valid, allow password reset
    return HTTPException(status_code=200, detail="OTP verified successfully. You may now reset your password.")


@app.post("/reset_password", tags=["Authentication"])
def reset_password(req: ResetPasswordRequest):
    """
    Resets the user's password after successful OTP verification.
    """

    user = user_auth.find_one({"email": req.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = hash_password(req.new_password)

    user_auth.update_one(
        {"email": req.email},
        {"$set": {"password_hash": hashed_password, "updated_at": datetime.now(timezone.utc)}}
    )

    otp_record.delete_one({"email": req.email})
    return {"message": "Password reset successfully"}


# --- Food Classification Endpoints ---
@app.post("/classify-food", 
         response_model=FoodClassificationResponse,
         responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
         tags=["Food Classification"])
async def classify_food_image(
    file: UploadFile = File(..., description="Image file containing Nigerian food"),
    current_user: dict = Depends(get_current_user)
):
    """
    Classify Nigerian food from an uploaded image.
    
    This endpoint accepts an image file and uses AI to identify Nigerian foods present in the image.
    It returns detailed information about detected foods including confidence scores and descriptions.
    
    - **file**: Image file (JPG, PNG, etc.) containing food to be classified
    - **Returns**: Detailed classification results including detected foods, confidence scores, and related food suggestions
    """
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image (JPG, PNG, etc.)"
        )
    
    # Check file size (limit to 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum allowed size is 10MB."
        )
    
    if len(file_content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded."
        )
    
    try:
        # Classify the image
        classification_result = classify_image(file_content)
        
        # Get related food suggestions if foods were detected
        detected_food_names = [food["name"] for food in classification_result.get("foods_detected", [])]
        related_foods = get_related_foods(detected_food_names) if detected_food_names else []
        
        # Add related foods to the result
        classification_result["related_foods"] = related_foods
        
        return classification_result
        
    except ValueError as e:
        # Handle image processing errors
        raise HTTPException(
            status_code=400,
            detail=f"Image processing error: {str(e)}"
        )
    except Exception as e:
        # Handle other classification errors
        raise HTTPException(
            status_code=500,
            detail=f"Classification service error: {str(e)}"
        )


@app.get("/food-categories", tags=["Food Classification"])
async def get_food_categories():
    """
    Get list of Nigerian food categories and examples.
    
    Returns information about different categories of Nigerian foods
    that can be detected by the classification system.
    """
    categories = {
        "main_dishes": {
            "description": "Primary meals and dishes",
            "examples": ["Jollof Rice", "Fried Rice", "Pounded Yam with Soup", "Amala and Ewedu"]
        },
        "soups": {
            "description": "Traditional Nigerian soups",
            "examples": ["Egusi Soup", "Ogbono Soup", "Bitter Leaf Soup", "Afang Soup", "Pepper Soup"]
        },
        "snacks": {
            "description": "Light meals and finger foods",
            "examples": ["Suya", "Akara", "Moi Moi", "Chin Chin", "Puff Puff"]
        },
        "side_dishes": {
            "description": "Accompanying dishes and sides",
            "examples": ["Plantain", "Bole", "Yam", "Sweet Potato"]
        },
        "drinks": {
            "description": "Traditional beverages",
            "examples": ["Palm Wine", "Zobo", "Kunu", "Tiger Nut Drink"]
        }
    }
    
    return {
        "categories": categories,
        "total_categories": len(categories),
        "message": "Nigerian food categories supported by the classification system"
    }
