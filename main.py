import os
import random
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from fastapi import FastAPI, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from bson import ObjectId
from auth.service import resend_otp_service
from auth.mail import send_email_otp, send_email_welcome
from pydantic import BaseModel, EmailStr as PydanticEmailStr, ValidationError
from pymongo import MongoClient
from bson.binary import Binary

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
)
from schemas.schema import (
    ClassificationPayload,
    RecipePayload,
    NutritionPayload,
    PurchasePayload,
)
# Auth DB
from config.database import otp_record, user_auth
# Features DB
from config.database import classification_requests

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
    """Handles new user registration and sends OTP for verification."""
    if user_exists_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if user_exists_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create the user
    new_user = create_user(user_data)
    
    try:
        # Generate OTP
        otp_code = generate_otp()
        
        # Store OTP in database
        otp_data = {
            "email": user_data.email,
            "otp": otp_code,
            "created_at": datetime.now(timezone.utc),
        }
        otp_record.insert_one(otp_data)
        
        # Send OTP email
        user_name = f"{user_data.firstname} {user_data.lastname}".strip()
        email_result = send_email_otp(
            receiver_email=user_data.email,
            otp_code=otp_code,
            expiry_minutes=5,
            user_name=user_name
        )
        
        # Check if email sending failed
        if not email_result.get("success", False):
            # Rollback: delete the OTP record if email fails
            otp_record.delete_one({"email": user_data.email})
            raise HTTPException(
                status_code=500, 
                detail=f"User created but failed to send OTP email: {email_result.get('message', 'Unknown error')}"
            )
        
        return {
            "message": "User created successfully! OTP sent to your email.",
            "user": new_user,
            "email_sent": True
        }
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # Handle any unexpected errors
        otp_record.delete_one({"email": user_data.email})
        raise HTTPException(
            status_code=500,
            detail=f"Error sending OTP: {str(e)}"
        )


@app.post("/verify", tags=["Authentication"])
def verify_user_account(otp_data: OTPVerifyRequest):
    """ Verify user account using OTP and send welcome email """

    otp_rec = otp_record.find_one({
        "email": otp_data.email,
        "otp": otp_data.otp
    })
    if not otp_rec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect OTP")

    OTP_EXPIRY_MINUTES = 5
    otp_age = datetime.now(timezone.utc) - otp_rec["created_at"]
    if otp_age > timedelta(minutes=OTP_EXPIRY_MINUTES):
        otp_record.delete_one({"email": otp_rec["email"]})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired. Please request a new one")

    user = user_auth.find_one({"email": otp_rec["email"]})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.get("is_verified") is True:
        otp_record.delete_one({"email": otp_rec["email"]})
        return {"message": "Account already verified"}

    set_verified = False
    try:
        # Mark verified
        user_auth.update_one({"email": user["email"]}, {
            "$set": {"is_verified": True, "updated_at": datetime.now(timezone.utc)}
        })
        set_verified = True

        # Send welcome email
        user_name = user.get('firstname', '').strip() or user.get("username", "there").strip()
        send_result = send_email_welcome(user_name=user_name, receiver=user["email"])

        ok = isinstance(send_result, dict) and send_result.get("status") == "success"
        if not ok:
            # Rollback verification and keep OTP so user can retry
            user_auth.update_one({"email": user["email"]}, {
                "$set": {"is_verified": False, "updated_at": datetime.now(timezone.utc)}
            })
            err_msg = (send_result or {}).get("message", "Failed to send welcome email")
            raise HTTPException(status_code=500, detail=f"Verification succeeded, but Welcome email failed: {err_msg}")

        # Success: delete OTP
        otp_record.delete_one({"email": otp_rec["email"]})
        return {"message": "Account verified successfully. Welcome email sent.", "email_sent": True}

    except HTTPException:
        raise
    except Exception as e:
        if set_verified:
            user_auth.update_one({"email": user["email"]}, {
                "$set": {"is_verified": False, "updated_at": datetime.now(timezone.utc)}
            })
        raise HTTPException(status_code=500, detail=f"Unexpected error during verification email: {str(e)}")



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


# Feature Enpoints

## Food Classification
@app.post("/features/food_classification", tags=["Features"])
async def food_classification(image: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """
    Accepts file upload (image) and returns classification result among other details.
    """
    try:
        img_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded image: {e}")

    if not img_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="Authenticated user has no email")

    try:
        payload = ClassificationPayload(email=user_email, image=img_bytes)
    except ValidationError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    # Main Implementation (with function calls)
    

    # Store request in DB
    try:
        doc = {
            "email": str(payload.email),
            "image": Binary(payload.image),
            "timestamp": payload.timestamp
        }

        result = classification_requests.insert_one(doc)
        return {"status": "success", "inserted_id": str(result.inserted_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save request to database: {e}")

## Recipe Generation
@app.post("/features/recipe_generation", tags=["Features"])
def recipe_generation(recipe_data: RecipePayload):
    """
    Accepts food name and other optional details, returns recipe suggestions
    """
    # Main Implementation

    # Store request in DB

    return

## Nutritional Values Generation
@app.post("/features/nutritional_estimates", tags=["Features"])
def nutritional_estimates(nutrition_data: NutritionPayload):
    """
    Accepts food name and other optional details, returns nutritional estimates
    """
    # Main Implementation

    # Store request in DB

    return

## Purchase Locations
@app.post("/features/purchase_locations", tags=["Features"])
def purchase_locations(purchase_data: PurchasePayload):
    """
    Accepts food name and location details, returns nearby purchase locations
    """
    # Main Implementation

    # Store request in DB


    return
