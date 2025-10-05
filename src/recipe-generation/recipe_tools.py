"""
Recipe Tools for Naija Nutri Hub

This module provides tools for generating and managing Nigerian food recipes
using external APIs and local databases.
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
class Recipe:
    """Data class for recipe information."""
    recipe_name: str
    description: str
    cuisine_type: str
    region: str
    difficulty: str
    prep_time: str
    cook_time: str
    total_time: str
    servings: str
    ingredients: List[Dict[str, str]]
    instructions: List[Dict[str, Union[int, str]]]
    cooking_tips: List[str]
    cultural_context: str
    nutritional_highlights: List[str]
    variations: List[Dict[str, str]]
    ingredient_substitutions: List[Dict[str, str]]


class NigerianRecipeDatabase:
    """
    Local database of traditional Nigerian recipes.
    Contains authentic recipes with proper ingredients and methods.
    """
    
    def __init__(self):
        self.recipes_db = {
            "jollof rice": {
                "recipe_name": "Nigerian Jollof Rice",
                "description": "Nigeria's most iconic rice dish cooked in a rich tomato-based sauce with spices",
                "cuisine_type": "Nigerian",
                "region": "National (with regional variations)",
                "difficulty": "Medium",
                "prep_time": "20 minutes",
                "cook_time": "45 minutes",
                "total_time": "65 minutes",
                "servings": "6-8 people",
                "ingredients": [
                    {"name": "Long grain rice", "quantity": "3", "unit": "cups", "notes": "parboiled preferred"},
                    {"name": "Fresh tomatoes", "quantity": "6", "unit": "large", "notes": "blanched and blended"},
                    {"name": "Red bell peppers", "quantity": "3", "unit": "medium", "notes": "blended with tomatoes"},
                    {"name": "Scotch bonnet pepper", "quantity": "1-2", "unit": "pieces", "notes": "adjust to taste"},
                    {"name": "Onions", "quantity": "2", "unit": "large", "notes": "diced"},
                    {"name": "Chicken stock", "quantity": "4-5", "unit": "cups", "notes": "or beef stock"},
                    {"name": "Vegetable oil", "quantity": "1/2", "unit": "cup", "notes": "palm oil optional"},
                    {"name": "Tomato paste", "quantity": "3", "unit": "tablespoons", "notes": ""},
                    {"name": "Curry powder", "quantity": "2", "unit": "teaspoons", "notes": ""},
                    {"name": "Thyme", "quantity": "1", "unit": "teaspoon", "notes": "dried or fresh"},
                    {"name": "Bay leaves", "quantity": "3", "unit": "pieces", "notes": ""},
                    {"name": "Salt", "quantity": "1", "unit": "teaspoon", "notes": "to taste"},
                    {"name": "Knorr cubes", "quantity": "2-3", "unit": "pieces", "notes": "seasoning cubes"}
                ],
                "instructions": [
                    {"step": 1, "instruction": "Wash and parboil rice until 70% done, drain and set aside", "time": "15 minutes"},
                    {"step": 2, "instruction": "Heat oil in a large pot and fry diced onions until golden", "time": "5 minutes"},
                    {"step": 3, "instruction": "Add tomato paste and fry until oil separates", "time": "3 minutes"},
                    {"step": 4, "instruction": "Add blended tomato and pepper mixture, cook until thick", "time": "15 minutes"},
                    {"step": 5, "instruction": "Add stock, curry powder, thyme, bay leaves, and seasoning", "time": "2 minutes"},
                    {"step": 6, "instruction": "Add parboiled rice, stir gently and cover", "time": "2 minutes"},
                    {"step": 7, "instruction": "Cook on medium heat for 20-25 minutes until rice is tender", "time": "25 minutes"},
                    {"step": 8, "instruction": "Stir occasionally, add more stock if needed", "time": ""},
                    {"step": 9, "instruction": "Let rest for 5 minutes before serving", "time": "5 minutes"}
                ],
                "cooking_tips": [
                    "The secret to good Jollof is the tomato base - cook it until oil separates",
                    "Use parboiled rice to prevent mushiness",
                    "Let the rice form a slight crust at the bottom for authentic flavor",
                    "Don't stir too often to avoid breaking the rice grains"
                ],
                "cultural_context": "Jollof Rice is Nigeria's national dish and source of friendly rivalry with Ghana and Senegal. It's a staple at celebrations, parties, and family gatherings.",
                "nutritional_highlights": [
                    "Good source of carbohydrates for energy",
                    "Contains lycopene from tomatoes",
                    "Provides vitamins from bell peppers"
                ],
                "variations": [
                    {"name": "Party Jollof", "description": "Cooked in large quantities over wood fire for smoky flavor"},
                    {"name": "Seafood Jollof", "description": "Made with fish or prawns instead of chicken stock"},
                    {"name": "Vegetarian Jollof", "description": "Uses vegetable stock and mixed vegetables"}
                ],
                "ingredient_substitutions": [
                    {"original": "Scotch bonnet pepper", "substitute": "Habanero pepper", "notes": "Similar heat level"},
                    {"original": "Palm oil", "substitute": "Vegetable oil", "notes": "Less authentic but acceptable"},
                    {"original": "Fresh tomatoes", "substitute": "Canned tomatoes", "notes": "Use good quality canned tomatoes"}
                ]
            },
            "egusi soup": {
                "recipe_name": "Traditional Egusi Soup",
                "description": "Rich Nigerian soup made from ground melon seeds, vegetables, and protein",
                "cuisine_type": "Nigerian",
                "region": "National (Yoruba origin)",
                "difficulty": "Medium",
                "prep_time": "30 minutes",
                "cook_time": "45 minutes",
                "total_time": "75 minutes",
                "servings": "6-8 people",
                "ingredients": [
                    {"name": "Ground egusi (melon seeds)", "quantity": "2", "unit": "cups", "notes": ""},
                    {"name": "Assorted meat", "quantity": "1", "unit": "kg", "notes": "beef, goat meat, etc."},
                    {"name": "Stockfish", "quantity": "4", "unit": "pieces", "notes": "soaked and cleaned"},
                    {"name": "Dried fish", "quantity": "3", "unit": "pieces", "notes": "cleaned and deboned"},
                    {"name": "Pumpkin leaves (ugu)", "quantity": "2", "unit": "cups", "notes": "chopped"},
                    {"name": "Spinach", "quantity": "2", "unit": "cups", "notes": "chopped"},
                    {"name": "Palm oil", "quantity": "1/2", "unit": "cup", "notes": ""},
                    {"name": "Onions", "quantity": "1", "unit": "large", "notes": "chopped"},
                    {"name": "Crayfish", "quantity": "3", "unit": "tablespoons", "notes": "ground"},
                    {"name": "Scotch bonnet pepper", "quantity": "2", "unit": "pieces", "notes": "chopped"},
                    {"name": "Locust beans (iru)", "quantity": "1", "unit": "tablespoon", "notes": "optional"},
                    {"name": "Knorr cubes", "quantity": "3", "unit": "pieces", "notes": ""},
                    {"name": "Salt", "quantity": "1", "unit": "teaspoon", "notes": "to taste"}
                ],
                "instructions": [
                    {"step": 1, "instruction": "Season and cook assorted meat until tender, reserve stock", "time": "30 minutes"},
                    {"step": 2, "instruction": "Heat palm oil in a large pot and fry chopped onions", "time": "5 minutes"},
                    {"step": 3, "instruction": "Add ground egusi and fry for 5 minutes, stirring constantly", "time": "5 minutes"},
                    {"step": 4, "instruction": "Gradually add meat stock while stirring to avoid lumps", "time": "5 minutes"},
                    {"step": 5, "instruction": "Add cooked meat, stockfish, and dried fish", "time": "2 minutes"},
                    {"step": 6, "instruction": "Add crayfish, pepper, locust beans, and seasoning", "time": "2 minutes"},
                    {"step": 7, "instruction": "Simmer for 15 minutes, stirring occasionally", "time": "15 minutes"},
                    {"step": 8, "instruction": "Add chopped vegetables and cook for 5 more minutes", "time": "5 minutes"},
                    {"step": 9, "instruction": "Adjust seasoning and serve hot", "time": "2 minutes"}
                ],
                "cooking_tips": [
                    "Fry the egusi properly to avoid lumps and develop flavor",
                    "Add stock gradually while stirring to maintain smooth consistency",
                    "Don't overcook the vegetables to maintain their color and nutrients",
                    "Use quality palm oil for authentic taste"
                ],
                "cultural_context": "Egusi soup is one of Nigeria's most popular soups, traditionally served with pounded yam, fufu, or rice. It's a symbol of hospitality and celebration.",
                "nutritional_highlights": [
                    "High in protein from meat and fish",
                    "Rich in vitamins A and C from vegetables",
                    "Good source of healthy fats from melon seeds"
                ],
                "variations": [
                    {"name": "Yoruba Style", "description": "With lots of vegetables and locust beans"},
                    {"name": "Igbo Style", "description": "Often includes bitter leaf and more fish"},
                    {"name": "Hausa Style", "description": "Sometimes made with groundnut paste addition"}
                ],
                "ingredient_substitutions": [
                    {"original": "Pumpkin leaves", "substitute": "Spinach", "notes": "Use more spinach if pumpkin leaves unavailable"},
                    {"original": "Stockfish", "substitute": "Smoked fish", "notes": "Different texture but similar flavor"},
                    {"original": "Locust beans", "substitute": "Bouillon cubes", "notes": "For umami flavor"}
                ]
            },
            "suya": {
                "recipe_name": "Nigerian Suya (Spiced Grilled Meat)",
                "description": "Popular Northern Nigerian street food - spiced grilled meat skewers",
                "cuisine_type": "Nigerian",
                "region": "Northern Nigeria (Hausa)",
                "difficulty": "Easy",
                "prep_time": "20 minutes",
                "cook_time": "15 minutes",
                "total_time": "35 minutes",
                "servings": "4-6 people",
                "ingredients": [
                    {"name": "Beef (sirloin or tenderloin)", "quantity": "1", "unit": "kg", "notes": "cut into strips"},
                    {"name": "Suya spice (yaji)", "quantity": "1/2", "unit": "cup", "notes": "or homemade blend"},
                    {"name": "Groundnut powder", "quantity": "1/4", "unit": "cup", "notes": "roasted and ground"},
                    {"name": "Ginger powder", "quantity": "1", "unit": "teaspoon", "notes": ""},
                    {"name": "Garlic powder", "quantity": "1", "unit": "teaspoon", "notes": ""},
                    {"name": "Cayenne pepper", "quantity": "2", "unit": "teaspoons", "notes": "adjust to taste"},
                    {"name": "Onion powder", "quantity": "1", "unit": "teaspoon", "notes": ""},
                    {"name": "Knorr cube", "quantity": "1", "unit": "piece", "notes": "crushed"},
                    {"name": "Salt", "quantity": "1/2", "unit": "teaspoon", "notes": ""},
                    {"name": "Vegetable oil", "quantity": "2", "unit": "tablespoons", "notes": "for basting"}
                ],
                "instructions": [
                    {"step": 1, "instruction": "Soak wooden skewers in water for 30 minutes", "time": "30 minutes"},
                    {"step": 2, "instruction": "Cut beef into thin strips about 1/4 inch thick", "time": "10 minutes"},
                    {"step": 3, "instruction": "Mix all spices together to make suya spice blend", "time": "5 minutes"},
                    {"step": 4, "instruction": "Thread meat onto skewers, leaving space between pieces", "time": "10 minutes"},
                    {"step": 5, "instruction": "Rub half the spice mix all over the meat", "time": "5 minutes"},
                    {"step": 6, "instruction": "Preheat grill to medium-high heat", "time": "5 minutes"},
                    {"step": 7, "instruction": "Grill skewers for 3-4 minutes per side", "time": "8 minutes"},
                    {"step": 8, "instruction": "Brush with oil and sprinkle remaining spices", "time": "2 minutes"},
                    {"step": 9, "instruction": "Serve immediately with sliced onions and tomatoes", "time": "2 minutes"}
                ],
                "cooking_tips": [
                    "Don't overcook the meat - it should be tender and juicy",
                    "Make your own yaji spice blend for authentic flavor",
                    "Use a meat thermometer to ensure proper doneness",
                    "Let meat rest at room temperature before grilling"
                ],
                "cultural_context": "Suya is a beloved Northern Nigerian street food, traditionally prepared by Hausa vendors. It's a popular evening snack and social food.",
                "nutritional_highlights": [
                    "High in protein from lean beef",
                    "Contains antioxidants from spices",
                    "Good source of iron and B vitamins"
                ],
                "variations": [
                    {"name": "Chicken Suya", "description": "Made with chicken instead of beef"},
                    {"name": "Fish Suya", "description": "Made with firm fish like mackerel"},
                    {"name": "Vegetarian Suya", "description": "Made with firm tofu or mushrooms"}
                ],
                "ingredient_substitutions": [
                    {"original": "Beef", "substitute": "Chicken thighs", "notes": "More tender than breast meat"},
                    {"original": "Suya spice", "substitute": "Homemade blend", "notes": "Mix groundnut, ginger, garlic, pepper"},
                    {"original": "Wooden skewers", "substitute": "Metal skewers", "notes": "No soaking required"}
                ]
            }
        }
    
    def get_recipe(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Get recipe data for a Nigerian dish."""
        return self.recipes_db.get(food_name.lower())
    
    def list_available_recipes(self) -> List[str]:
        """Get list of recipes available in the local database."""
        return list(self.recipes_db.keys())
    
    def search_recipes_by_ingredient(self, ingredient: str) -> List[str]:
        """Search for recipes containing a specific ingredient."""
        matching_recipes = []
        for recipe_name, recipe_data in self.recipes_db.items():
            ingredients = recipe_data.get("ingredients", [])
            for ing in ingredients:
                if ingredient.lower() in ing.get("name", "").lower():
                    matching_recipes.append(recipe_name)
                    break
        return matching_recipes


class TheMealDBAPI:
    """
    Integration with TheMealDB API for additional recipe data.
    """
    
    def __init__(self):
        self.base_url = "https://www.themealdb.com/api/json/v1/1"
    
    def search_recipe(self, food_name: str) -> Optional[Dict[str, Any]]:
        """Search for recipe using TheMealDB API."""
        try:
            search_url = f"{self.base_url}/search.php"
            params = {"s": food_name}
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("meals"):
                return data["meals"][0]  # Return first match
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching recipe from TheMealDB: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TheMealDB API: {e}")
            return None
    
    def get_random_recipe(self) -> Optional[Dict[str, Any]]:
        """Get a random recipe from TheMealDB."""
        try:
            random_url = f"{self.base_url}/random.php"
            response = requests.get(random_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("meals"):
                return data["meals"][0]
            return None
            
        except Exception as e:
            logger.error(f"Error fetching random recipe: {e}")
            return None


class RecipeGenerator:
    """
    Main recipe generation class that combines local database and external APIs.
    """
    
    def __init__(self):
        self.nigerian_db = NigerianRecipeDatabase()
        self.mealdb_api = TheMealDBAPI()
    
    def generate_recipe(self, food_name: str) -> Optional[Recipe]:
        """
        Generate a recipe for a given food name.
        
        Args:
            food_name: Name of the dish
            
        Returns:
            Recipe object with complete recipe information
        """
        # First try local Nigerian database
        recipe_data = self.nigerian_db.get_recipe(food_name)
        
        # If not found locally, try external API
        if not recipe_data:
            api_data = self.mealdb_api.search_recipe(food_name)
            if api_data:
                recipe_data = self._parse_mealdb_data(api_data)
        
        if not recipe_data:
            return None
        
        return Recipe(**recipe_data)
    
    def _parse_mealdb_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TheMealDB API response into our standard format."""
        try:
            # Extract ingredients
            ingredients = []
            for i in range(1, 21):  # TheMealDB has up to 20 ingredients
                ingredient = api_data.get(f"strIngredient{i}")
                measure = api_data.get(f"strMeasure{i}")
                if ingredient and ingredient.strip():
                    ingredients.append({
                        "name": ingredient.strip(),
                        "quantity": measure.strip() if measure else "",
                        "unit": "",
                        "notes": ""
                    })
            
            # Parse instructions
            instructions_text = api_data.get("strInstructions", "")
            instruction_steps = []
            for i, step in enumerate(instructions_text.split(". "), 1):
                if step.strip():
                    instruction_steps.append({
                        "step": i,
                        "instruction": step.strip(),
                        "time": ""
                    })
            
            return {
                "recipe_name": api_data.get("strMeal", "Unknown Recipe"),
                "description": f"Recipe for {api_data.get('strMeal', 'Unknown')}",
                "cuisine_type": api_data.get("strArea", "International"),
                "region": api_data.get("strArea", ""),
                "difficulty": "Medium",
                "prep_time": "20 minutes",
                "cook_time": "30 minutes",
                "total_time": "50 minutes",
                "servings": "4 people",
                "ingredients": ingredients,
                "instructions": instruction_steps,
                "cooking_tips": ["Follow instructions carefully", "Adjust seasoning to taste"],
                "cultural_context": f"Traditional {api_data.get('strArea', 'International')} dish",
                "nutritional_highlights": ["Varies by ingredients"],
                "variations": [],
                "ingredient_substitutions": []
            }
        except Exception as e:
            logger.error(f"Error parsing MealDB data: {e}")
            return {}
    
    def get_recipe_suggestions(self, ingredients: List[str]) -> List[str]:
        """Get recipe suggestions based on available ingredients."""
        suggestions = []
        for ingredient in ingredients:
            matching_recipes = self.nigerian_db.search_recipes_by_ingredient(ingredient)
            suggestions.extend(matching_recipes)
        
        # Remove duplicates and return unique suggestions
        return list(set(suggestions))
    
    def get_cooking_tips(self, food_name: str) -> List[str]:
        """Get cooking tips for a specific dish."""
        recipe_data = self.nigerian_db.get_recipe(food_name)
        if recipe_data:
            return recipe_data.get("cooking_tips", [])
        return ["Use fresh ingredients", "Follow cooking times carefully", "Taste and adjust seasoning"]
    
    def get_ingredient_substitutions(self, food_name: str) -> List[Dict[str, str]]:
        """Get ingredient substitutions for a dish."""
        recipe_data = self.nigerian_db.get_recipe(food_name)
        if recipe_data:
            return recipe_data.get("ingredient_substitutions", [])
        return []


# Global instances
recipe_generator = RecipeGenerator()


def generate_recipe(food_name: str) -> Optional[Dict[str, Any]]:
    """
    Generate a recipe for a Nigerian dish.
    
    Args:
        food_name: Name of the dish
        
    Returns:
        Complete recipe information
    """
    recipe = recipe_generator.generate_recipe(food_name)
    if recipe:
        return recipe.__dict__
    return None


def get_recipe_suggestions(ingredients: List[str]) -> List[str]:
    """
    Get recipe suggestions based on available ingredients.
    
    Args:
        ingredients: List of available ingredients
        
    Returns:
        List of suggested recipe names
    """
    return recipe_generator.get_recipe_suggestions(ingredients)


def get_cooking_tips(food_name: str) -> List[str]:
    """
    Get cooking tips for a specific dish.
    
    Args:
        food_name: Name of the dish
        
    Returns:
        List of cooking tips
    """
    return recipe_generator.get_cooking_tips(food_name)


def get_available_recipes() -> List[str]:
    """Get list of recipes available in the database."""
    return recipe_generator.nigerian_db.list_available_recipes()


def search_recipes_by_ingredient(ingredient: str) -> List[str]:
    """
    Search for recipes containing a specific ingredient.
    
    Args:
        ingredient: Ingredient to search for
        
    Returns:
        List of recipe names containing the ingredient
    """
    return recipe_generator.nigerian_db.search_recipes_by_ingredient(ingredient)
