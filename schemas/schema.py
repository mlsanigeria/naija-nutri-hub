from bson import ObjectId
from typing import Optional, List, Dict
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

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=6, max_length=20)


# Food Classification Models
class FoodItem(BaseModel):
    name: str = Field(..., description="Name of the detected food")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for detection")
    description: str = Field(..., description="Brief description of the food")
    category: str = Field(..., description="Category of food (main_dish, soup, snack, side_dish, drink)")


class FoodClassificationResponse(BaseModel):
    foods_detected: List[FoodItem] = Field(..., description="List of detected foods")
    is_nigerian_food: bool = Field(..., description="Whether Nigerian food was detected")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    additional_notes: str = Field(..., description="Additional observations")
    related_foods: Optional[List[Dict[str, str]]] = Field(None, description="Suggested related foods")


class FoodSuggestion(BaseModel):
    name: str = Field(..., description="Name of suggested food")
    description: str = Field(..., description="Description of the food")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: str = Field(..., description="Detailed error information")
