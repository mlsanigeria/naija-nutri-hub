"""
Nutrition Tools for Naija Nutri Hub

This module provides tools for retrieving and calculating nutritional information
for Nigerian foods using various APIs and databases.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NutritionInfo:
    """Data class for nutritional information."""
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    fiber: float
    sugar: float
    sodium: float
    cholesterol: float
    vitamins: Dict[str, float]
    minerals: Dict[str, float]
    serving_size: str = "100g"


class NigerianFoodNutritionDB:
    """
    Local database of Nigerian food nutritional information.
    Contains traditional Nigerian foods with their typical nutritional values.
    """
    
    def __init__(self):
        self.foods_db = {
            "jollof rice": {
                "calories": 166,
                "protein": 3.2,
                "carbohydrates": 28.5,
                "fat": 4.8,
                "fiber": 1.2,
                "sugar": 2.1,
                "sodium": 250,
                "cholesterol": 0,
                "vitamins": {
                    "vitamin_c": 15.0,
                    "vitamin_a": 180.0,
                    "thiamine": 0.12,
                    "niacin": 1.8
                },
                "minerals": {
                    "iron": 1.2,
                    "calcium": 18,
                    "potassium": 165,
                    "phosphorus": 58
                }
            },
            "egusi soup": {
                "calories": 145,
                "protein": 8.5,
                "carbohydrates": 6.2,
                "fat": 10.8,
                "fiber": 3.2,
                "sugar": 2.8,
                "sodium": 320,
                "cholesterol": 25,
                "vitamins": {
                    "vitamin_c": 35.0,
                    "vitamin_a": 450.0,
                    "folate": 68.0,
                    "vitamin_k": 85.0
                },
                "minerals": {
                    "iron": 3.5,
                    "calcium": 125,
                    "magnesium": 45,
                    "zinc": 1.8
                }
            },
            "pounded yam": {
                "calories": 118,
                "protein": 1.5,
                "carbohydrates": 27.9,
                "fat": 0.17,
                "fiber": 4.1,
                "sugar": 0.5,
                "sodium": 9,
                "cholesterol": 0,
                "vitamins": {
                    "vitamin_c": 17.1,
                    "vitamin_b6": 0.29,
                    "thiamine": 0.11,
                    "folate": 23.0
                },
                "minerals": {
                    "potassium": 816,
                    "manganese": 0.4,
                    "copper": 0.18,
                    "magnesium": 21
                }
            },
            "suya": {
                "calories": 265,
                "protein": 26.2,
                "carbohydrates": 3.1,
                "fat": 16.8,
                "fiber": 1.2,
                "sugar": 1.8,
                "sodium": 520,
                "cholesterol": 78,
                "vitamins": {
                    "vitamin_b12": 2.6,
                    "niacin": 8.9,
                    "vitamin_b6": 0.52,
                    "riboflavin": 0.21
                },
                "minerals": {
                    "iron": 3.2,
                    "zinc": 4.8,
                    "phosphorus": 201,
                    "selenium": 26.4
                }
            },
            "akara": {
                "calories": 185,
                "protein": 8.1,
                "carbohydrates": 12.5,
                "fat": 12.2,
                "fiber": 4.5,
                "sugar": 2.1,
                "sodium": 280,
                "cholesterol": 0,
                "vitamins": {
                    "folate": 145.0,
                    "thiamine": 0.31,
                    "vitamin_k": 15.0,
                    "vitamin_e": 2.8
                },
                "minerals": {
                    "iron": 2.8,
                    "calcium": 65,
                    "magnesium": 58,
                    "phosphorus": 125
                }
            },
            "moi moi": {
                "calories": 122,
                "protein": 9.8,
                "carbohydrates": 8.5,
                "fat": 5.2,
                "fiber": 5.8,
                "sugar": 1.2,
                "sodium": 185,
                "cholesterol": 12,
                "vitamins": {
                    "folate": 125.0,
                    "vitamin_b6": 0.18,
                    "thiamine": 0.25,
                    "riboflavin": 0.15
                },
                "minerals": {
                    "iron": 2.1,
                    "calcium": 48,
                    "magnesium": 42,
                    "potassium": 285
                }
            },
            "plantain": {
                "calories": 89,
                "protein": 1.3,
                "carbohydrates": 22.8,
                "fat": 0.37,
                "fiber": 2.3,
                "sugar": 12.2,
                "sodium": 4,
                "cholesterol": 0,
                "vitamins": {
                    "vitamin_c": 18.4,
                    "vitamin_a": 115.0,
                    "vitamin_b6": 0.30,
                    "folate": 20.0
                },
                "minerals": {
                    "potassium": 499,
                    "magnesium": 37,
                    "phosphorus": 34,
                    "iron": 0.6
                }
            }
        }
    
    def get_nutrition(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Get nutrition data for a Nigerian food item."""
        return self.foods_db.get(food_name.lower())
    
    def list_available_foods(self) -> List[str]:
        """Get list of foods available in the local database."""
        return list(self.foods_db.keys())


class SpoonacularNutritionAPI:
    """
    Integration with Spoonacular API for additional nutritional data.
    """
    
    def __init__(self):
        self.api_key = os.getenv("SPOONACULAR_API_KEY")
        self.base_url = "https://api.spoonacular.com/food"
    
    def search_food_nutrition(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Search for nutritional information using Spoonacular API."""
        if not self.api_key:
            logger.warning("Spoonacular API key not found")
            return None
        
        try:
            # Search for the food item
            search_url = f"{self.base_url}/ingredients/search"
            search_params = {
                "query": food_name,
                "apiKey": self.api_key,
                "number": 1
            }
            
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if not search_data.get("results"):
                return None
            
            ingredient_id = search_data["results"][0]["id"]
            
            # Get nutrition information
            nutrition_url = f"{self.base_url}/ingredients/{ingredient_id}/information"
            nutrition_params = {
                "apiKey": self.api_key,
                "amount": 100,
                "unit": "grams"
            }
            
            nutrition_response = requests.get(nutrition_url, params=nutrition_params, timeout=10)
            nutrition_response.raise_for_status()
            
            return nutrition_response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error fetching nutrition data from Spoonacular: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Spoonacular API: {e}")
            return None


class NutritionCalculator:
    """
    Calculator for nutritional values with Nigerian food considerations.
    """
    
    def __init__(self):
        self.nigerian_db = NigerianFoodNutritionDB()
        self.spoonacular = SpoonacularNutritionAPI()
    
    def calculate_nutrition(self, food_name: str, serving_size: float = 100) -> Optional[NutritionInfo]:
        """
        Calculate nutritional information for a given food and serving size.
        
        Args:
            food_name: Name of the food item
            serving_size: Serving size in grams (default: 100g)
            
        Returns:
            NutritionInfo object with calculated values
        """
        # First try local Nigerian database
        nutrition_data = self.nigerian_db.get_nutrition(food_name)
        
        # If not found, try Spoonacular API
        if not nutrition_data:
            api_data = self.spoonacular.search_food_nutrition(food_name)
            if api_data:
                nutrition_data = self._parse_spoonacular_data(api_data)
        
        if not nutrition_data:
            return None
        
        # Scale nutrition values based on serving size
        scale_factor = serving_size / 100  # Base data is per 100g
        
        return NutritionInfo(
            calories=nutrition_data["calories"] * scale_factor,
            protein=nutrition_data["protein"] * scale_factor,
            carbohydrates=nutrition_data["carbohydrates"] * scale_factor,
            fat=nutrition_data["fat"] * scale_factor,
            fiber=nutrition_data["fiber"] * scale_factor,
            sugar=nutrition_data["sugar"] * scale_factor,
            sodium=nutrition_data["sodium"] * scale_factor,
            cholesterol=nutrition_data["cholesterol"] * scale_factor,
            vitamins={k: v * scale_factor for k, v in nutrition_data["vitamins"].items()},
            minerals={k: v * scale_factor for k, v in nutrition_data["minerals"].items()},
            serving_size=f"{serving_size}g"
        )
    
    def _parse_spoonacular_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Spoonacular API response into our standard format."""
        try:
            nutrition = api_data.get("nutrition", {})
            nutrients = {n["name"].lower(): n["amount"] for n in nutrition.get("nutrients", [])}
            
            return {
                "calories": nutrients.get("calories", 0),
                "protein": nutrients.get("protein", 0),
                "carbohydrates": nutrients.get("carbohydrates", 0),
                "fat": nutrients.get("fat", 0),
                "fiber": nutrients.get("fiber", 0),
                "sugar": nutrients.get("sugar", 0),
                "sodium": nutrients.get("sodium", 0),
                "cholesterol": nutrients.get("cholesterol", 0),
                "vitamins": {
                    "vitamin_c": nutrients.get("vitamin c", 0),
                    "vitamin_a": nutrients.get("vitamin a", 0),
                    "folate": nutrients.get("folate", 0),
                    "vitamin_b6": nutrients.get("vitamin b6", 0)
                },
                "minerals": {
                    "iron": nutrients.get("iron", 0),
                    "calcium": nutrients.get("calcium", 0),
                    "potassium": nutrients.get("potassium", 0),
                    "magnesium": nutrients.get("magnesium", 0)
                }
            }
        except Exception as e:
            logger.error(f"Error parsing Spoonacular data: {e}")
            return {}
    
    def calculate_meal_nutrition(self, foods: List[Dict[str, Union[str, float]]]) -> Dict[str, Any]:
        """
        Calculate total nutrition for a meal with multiple foods.
        
        Args:
            foods: List of dicts with 'name' and 'serving_size' keys
            
        Returns:
            Combined nutritional information
        """
        total_nutrition = {
            "calories": 0,
            "protein": 0,
            "carbohydrates": 0,
            "fat": 0,
            "fiber": 0,
            "sugar": 0,
            "sodium": 0,
            "cholesterol": 0,
            "vitamins": {},
            "minerals": {}
        }
        
        food_details = []
        
        for food_item in foods:
            nutrition = self.calculate_nutrition(
                food_item["name"], 
                food_item.get("serving_size", 100)
            )
            
            if nutrition:
                # Add to totals
                total_nutrition["calories"] += nutrition.calories
                total_nutrition["protein"] += nutrition.protein
                total_nutrition["carbohydrates"] += nutrition.carbohydrates
                total_nutrition["fat"] += nutrition.fat
                total_nutrition["fiber"] += nutrition.fiber
                total_nutrition["sugar"] += nutrition.sugar
                total_nutrition["sodium"] += nutrition.sodium
                total_nutrition["cholesterol"] += nutrition.cholesterol
                
                # Combine vitamins and minerals
                for vitamin, value in nutrition.vitamins.items():
                    total_nutrition["vitamins"][vitamin] = total_nutrition["vitamins"].get(vitamin, 0) + value
                
                for mineral, value in nutrition.minerals.items():
                    total_nutrition["minerals"][mineral] = total_nutrition["minerals"].get(mineral, 0) + value
                
                food_details.append({
                    "name": food_item["name"],
                    "serving_size": nutrition.serving_size,
                    "nutrition": nutrition.__dict__
                })
        
        return {
            "total_nutrition": total_nutrition,
            "individual_foods": food_details,
            "meal_summary": {
                "total_calories": total_nutrition["calories"],
                "macronutrient_breakdown": {
                    "protein_percentage": round((total_nutrition["protein"] * 4 / total_nutrition["calories"]) * 100, 1) if total_nutrition["calories"] > 0 else 0,
                    "carbs_percentage": round((total_nutrition["carbohydrates"] * 4 / total_nutrition["calories"]) * 100, 1) if total_nutrition["calories"] > 0 else 0,
                    "fat_percentage": round((total_nutrition["fat"] * 9 / total_nutrition["calories"]) * 100, 1) if total_nutrition["calories"] > 0 else 0
                }
            }
        }


class HealthAnalyzer:
    """
    Analyzer for health benefits and dietary considerations of Nigerian foods.
    """
    
    def __init__(self):
        self.health_benefits = {
            "jollof rice": {
                "benefits": ["Energy source", "Contains antioxidants from tomatoes", "Provides B vitamins"],
                "concerns": ["High in calories", "May contain excess sodium"],
                "dietary_compatibility": {
                    "diabetic": "moderate - watch portion size",
                    "hypertensive": "caution - high sodium content",
                    "weight_loss": "moderate - control portions"
                }
            },
            "egusi soup": {
                "benefits": ["High protein content", "Rich in vitamins A and C", "Good source of healthy fats"],
                "concerns": ["High calorie content", "May be high in saturated fat"],
                "dietary_compatibility": {
                    "diabetic": "good - low carb, high protein",
                    "hypertensive": "moderate - watch salt content",
                    "weight_loss": "good - high protein, satisfying"
                }
            }
        }
    
    def analyze_health_impact(self, food_name: str) -> Dict[str, Any]:
        """Analyze health benefits and considerations for a food."""
        return self.health_benefits.get(food_name.lower(), {
            "benefits": ["Nutritional analysis available"],
            "concerns": ["Consult nutritionist for specific dietary needs"],
            "dietary_compatibility": {
                "diabetic": "consult healthcare provider",
                "hypertensive": "consult healthcare provider", 
                "weight_loss": "consider portion sizes"
            }
        })


# Global instances
nutrition_calculator = NutritionCalculator()
health_analyzer = HealthAnalyzer()


def get_food_nutrition(food_name: str, serving_size: float = 100) -> Optional[Dict[str, Any]]:
    """
    Get nutritional information for a Nigerian food item.
    
    Args:
        food_name: Name of the food
        serving_size: Serving size in grams
        
    Returns:
        Nutritional information dictionary
    """
    nutrition = nutrition_calculator.calculate_nutrition(food_name, serving_size)
    if nutrition:
        return nutrition.__dict__
    return None


def analyze_meal_nutrition(foods: List[Dict[str, Union[str, float]]]) -> Dict[str, Any]:
    """
    Analyze nutrition for a complete meal.
    
    Args:
        foods: List of food items with serving sizes
        
    Returns:
        Complete meal nutritional analysis
    """
    return nutrition_calculator.calculate_meal_nutrition(foods)


def get_health_analysis(food_name: str) -> Dict[str, Any]:
    """
    Get health benefits and dietary considerations for a food.
    
    Args:
        food_name: Name of the food
        
    Returns:
        Health analysis information
    """
    return health_analyzer.analyze_health_impact(food_name)


def get_available_foods() -> List[str]:
    """Get list of foods available in the nutrition database."""
    return nutrition_calculator.nigerian_db.list_available_foods()
