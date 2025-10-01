from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
from bson import ObjectId

# Authentication
from auth.mail import send_email_otp
from auth.service import (create_user, generate_otp, get_user_via_email,
                          get_user_via_username, user_exists_email,
                          user_exists_username, user_serializer)

from auth.utils import hash_password, verify_password

# Schema/Database
from schemas.schema import (LoginRequest, OTPModel, OTPVerifyRequest,
                            ResetPasswordRequest, UserCreate)
from config.database import otp_record, user_auth

import random
import uuid

app = FastAPI(
    title = "Naija Nutri Hub API",
    description = "Backend API documentation for the Naija Nutri Hub project",
    version = "1.0.0"
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
def sign_up(user_data: UserCreate):
    """
    Create a new user account
    
    Args:
        user_data (UserCreate): User registration data
        
    Returns:
        dict: Success message and user data (without password)
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    try:
        # Create user using the service function
        created_user = create_user(user_data)
        
        return {
            "message": "User created successfully",
            "user": created_user,
            "status": "success"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like duplicate email/username)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/verify", tags=["Authentication"])
def verify_user_account(otp_data: OTPVerifyRequest):
    return

@app.post("/resend_otp", tags=["Authentication"])
def resend_otp(email: str):
    return
    
@app.post("/login", tags=["Authentication"])
def login_user(user: LoginRequest):
    return

@app.post("/reset_password", tags=["authentication"])
def reset_password(user: ResetPasswordRequest):
    return
