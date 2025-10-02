from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

# Authentication
from auth.mail import send_email_otp
from auth.service import (
    create_user as create_user_db, 
    generate_otp, 
    get_user_via_email,
    get_user_via_username, 
    user_exists_email,
    user_exists_username, 
    user_serializer
)
from auth.utils import hash_password, verify_password
from auth.jwt import create_access_token, decode_access_token, TokenData # New JWT imports

# Schema/Database
from schemas.schema import (LoginRequest, OTPModel, OTPVerifyRequest,
                            ResetPasswordRequest, UserCreate)
from config.database import otp_record, user_auth

import random
import uuid
from datetime import datetime, timedelta

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

# --- JWT DEPENDENCY ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependency function to validate JWT and fetch user data.
    """
    token_data: TokenData = decode_access_token(token)
    
    user = get_user_via_email(token_data.email)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Home
@app.get("/", tags=["Home"])
def index():
    return {"Project": "Naija Nutri Hub"}

# --- PROTECTED EXAMPLE ---
@app.get("/user/me", tags=["User"], response_model=None)
def read_users_me(current_user: dict = Depends(get_current_user)):
    """A protected route that requires a valid JWT."""
    return {"message": "Authenticated successfully!", "user": current_user}

# Create new user
@app.post("/sign-up", tags=["Authentication"])
def create_user_endpoint(user_data: UserCreate):
    # 1. Check for existing users
    if user_exists_email(user_data.email):
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    if user_exists_username(user_data.username):
        raise HTTPException(status_code=400, detail="User with this username already exists.")

    # 2. Hash the password and prepare data
    user_dict = user_data.model_dump()
    user_dict["password"] = hash_password(user_data.password)
    user_dict["is_verified"] = False
    
    # 3. Save the user
    new_user = create_user_db(user_dict)
    
    if not new_user:
        raise HTTPException(status_code=500, detail="User creation failed due to a server error.")
        
    # 4. Generate, save, and send OTP
    otp_code = generate_otp(length=6) 
    
    otp_record.delete_one({"email": user_data.email}) 

    otp_data = OTPModel(email=user_data.email, otp=otp_code)
    otp_record.insert_one(otp_data.model_dump())
    
    send_email_otp(user_data.email, otp_code)

    return {
        "status": "success",
        "message": "User created. Check your email for an OTP to verify your account.",
        "user_id": str(new_user.inserted_id)
    }

@app.post("/verify", tags=["Authentication"])
def verify_user_account(otp_data: OTPVerifyRequest):
    # 1. Find the OTP record
    otp_record_document = otp_record.find_one({"email": otp_data.email})
    
    if not otp_record_document:
        raise HTTPException(status_code=400, detail="Invalid email or OTP not found. Please re-request OTP.")

    # 2. Compare the OTPs
    if otp_record_document.get("otp") != otp_data.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP provided.")

    # 3. OTP is correct: Update the user's verification status
    update_result = user_auth.update_one(
        {"email": otp_data.email},
        {"$set": {"is_verified": True}}
    )
    
    if update_result.matched_count == 0:
         raise HTTPException(status_code=404, detail="User not found for verification.")

    # 4. Clean up: Delete the used OTP record
    otp_record.delete_one({"email": otp_data.email})

    return {
        "status": "success",
        "message": "Account successfully verified and activated."
    }

@app.post("/resend_otp", tags=["Authentication"])
def resend_otp_endpoint(email: str):
    # 1. Check if user exists
    user_data = get_user_via_email(email)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if user_data.get("is_verified"):
        return {"status": "info", "message": "Account is already verified."}

    # 2. Generate new OTP and update record
    otp_code = generate_otp(length=6)
    
    otp_record.delete_one({"email": email}) 

    otp_data = OTPModel(email=email, otp=otp_code)
    otp_record.insert_one(otp_data.model_dump())
    
    # 3. Send the new OTP
    send_email_otp(email, otp_code)

    return {
        "status": "success",
        "message": "New OTP has been sent to your email."
    }
    
@app.post("/login", tags=["Authentication"])
def login_user_endpoint(user_credentials: LoginRequest):
    # 1. Retrieve user by email 
    raw_user_doc = user_auth.find_one({"email": user_credentials.email}) 
    
    if not raw_user_doc:
        raise HTTPException(status_code=401, detail="Invalid login credentials.")

    # 2. Verify password
    if not verify_password(user_credentials.password, raw_user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid login credentials.")
        
    # 3. Check verification status
    if not raw_user_doc.get("is_verified"):
        raise HTTPException(
            status_code=403, 
            detail="Account not verified. Please verify your email with the OTP first."
        )
        
    # 4. Success: Generate and return a token
    access_token_data = {
        "user_id": str(raw_user_doc["_id"]),
        "email": raw_user_doc["email"]
    }
    
    access_token = create_access_token(data=access_token_data)
    
    return {
        "status": "success",
        "message": "Login successful.",
        "user_id": str(raw_user_doc["_id"]),
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/reset_password", tags=["authentication"])
def reset_password(user: ResetPasswordRequest):
    return {"message": "Password reset logic placeholder"}