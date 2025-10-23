from bson import ObjectId
from typing import Optional, List
from datetime import datetime
from typing import Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator
# from bson.binary import Binary


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

# Endpoint-specific payloads

# Sample structure for storing classification request in db
class ClassificationPayload(BaseModel):
    email: EmailStr
    image: bytes
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RecipePayload(BaseModel):
    email: EmailStr
    food_name: str
    servings: Optional[float] = None  # e.g. "3 plates/portions"
    dietary_restriction: Optional[List[str]] = None # e.g ["Vegetarian", "Vegan", "Lactose intolerant", "Gluten-free", "Nut allergy", "Diabetic", "Halal"]
    extra_inputs: Optional[str] = None             # e.g. Preferred Cuisine is "yoruba etc.
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class NutritionPayload(BaseModel):
    email: EmailStr
    food_name: str
    portion_size: Optional[str] = None              # e.g. "1 cup", "200g"
    extra_inputs: Optional[str] = None             # e.g. Preferred Cuisine is "yoruba etc.
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PurchasePayload(BaseModel):
    email: EmailStr
    food_name: str
    location_query: Optional[str] = None            # e.g. "Surulere, Lagos"
    max_distance_km: Optional[float] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)