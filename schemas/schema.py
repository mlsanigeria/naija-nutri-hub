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


# Nutritional Facts Models
class BasicNutrition(BaseModel):
    calories: float = Field(..., description="Calories per serving")
    protein: float = Field(..., description="Protein in grams")
    carbohydrates: float = Field(..., description="Carbohydrates in grams")
    fat: float = Field(..., description="Fat in grams")
    fiber: float = Field(..., description="Fiber in grams")
    sugar: float = Field(..., description="Sugar in grams")
    sodium: float = Field(..., description="Sodium in milligrams")
    cholesterol: float = Field(..., description="Cholesterol in milligrams")
    vitamins: Dict[str, float] = Field(..., description="Vitamins content")
    minerals: Dict[str, float] = Field(..., description="Minerals content")
    serving_size: str = Field(..., description="Serving size")


class HealthAnalysis(BaseModel):
    benefits: List[str] = Field(..., description="Health benefits")
    concerns: List[str] = Field(..., description="Health concerns")
    dietary_compatibility: Dict[str, str] = Field(..., description="Dietary compatibility info")


class NutritionalFactsResponse(BaseModel):
    food_name: str = Field(..., description="Name of the food")
    serving_size: str = Field(..., description="Serving size")
    basic_nutrition: Optional[BasicNutrition] = Field(None, description="Basic nutritional information")
    health_analysis: Optional[HealthAnalysis] = Field(None, description="Health analysis")
    ai_insights: Optional[Dict[str, Any]] = Field(None, description="AI-generated insights")
    data_sources: Dict[str, bool] = Field(..., description="Data sources used")
    recommendations: List[str] = Field(..., description="Personalized recommendations")


class MealItem(BaseModel):
    name: str = Field(..., description="Name of the food item")
    serving_size: float = Field(..., description="Serving size in grams", gt=0)


class MealNutritionRequest(BaseModel):
    foods: List[MealItem] = Field(..., description="List of food items in the meal")


class MealNutritionResponse(BaseModel):
    meal_composition: List[str] = Field(..., description="Foods in the meal")
    total_nutrition: Dict[str, Any] = Field(..., description="Total nutritional content")
    individual_foods: List[Dict[str, Any]] = Field(..., description="Individual food nutrition")
    meal_summary: Dict[str, Any] = Field(..., description="Meal summary statistics")
    ai_insights: Optional[Dict[str, Any]] = Field(None, description="AI insights for the meal")
    meal_recommendations: List[str] = Field(..., description="Meal-specific recommendations")
    cultural_context: Dict[str, Any] = Field(..., description="Cultural context of the meal")


class FoodComparisonRequest(BaseModel):
    foods: List[str] = Field(..., description="List of food names to compare", min_items=2)


class FoodComparisonResponse(BaseModel):
    foods_compared: List[str] = Field(..., description="Foods that were compared")
    individual_nutrition: Dict[str, Any] = Field(..., description="Individual nutrition data")
    comparisons: Dict[str, str] = Field(..., description="Comparison results")
    ai_analysis: Optional[Dict[str, Any]] = Field(None, description="AI comparison analysis")
    recommendations: List[str] = Field(..., description="Comparison-based recommendations")
