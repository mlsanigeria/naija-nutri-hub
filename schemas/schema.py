from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator

class User(BaseModel):
    firstname: str = Field(...)
    lastname: str = Field(...)
    username: str
    email: EmailStr
    password_hash: str
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_used: datetime

class UserCreate(BaseModel):
    firstname: str = Field(...)
    lastname: str = Field(...)
    username: str = Field(...)
    referral_code: Optional[str] = Field(default=None)
    email: EmailStr = Field(max_length=50)
    password: str = Field(min_length=6, max_length=20)

class OTPModel(BaseModel):
    email: EmailStr
    otp: str
    created_at: datetime

    
class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class LoginRequest(BaseModel):
    username_email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    """Schema for requesting a password reset email."""
    email: str

class ResetPasswordPayload(BaseModel):
    """
    Schema for resetting the password using a token.
    This replaces the original ResetPasswordRequest if it 
    was just an email/password combination.
    """
    token: str
    new_password: str = Field(..., min_length=8)

