"""
nutrition_tools.py
------------------
Grounds nutritional data using provided datasets and APIs:
- TheMealDB (https://www.themealdb.com/api.php)
- Spoonacular (https://spoonacular.com/food-api)
"""

import os
import requests
import json
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

# Load API keys from .env
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")



#  1. TheMealDB 
def get_nutrition_from_mealdb(food_name: str) -> dict:
    """
    Get basic meal information (ingredients, category, area) from TheMealDB.
    Note: TheMealDB does not return full nutrition, so we use this as grounding context.
    """
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data["meals"]:
            return {"source": "TheMealDB", "food_name": food_name, "data_found": False}

        meal = data["meals"][0]
        ingredients = []
        for i in range(1, 21):
            ingredient = meal.get(f"strIngredient{i}")
            measure = meal.get(f"strMeasure{i}")
            if ingredient and ingredient.strip():
                ingredients.append({"ingredient": ingredient, "measure": measure})

        return {
            "source": "TheMealDB",
            "food_name": meal["strMeal"],
            "category": meal.get("strCategory"),
            "area": meal.get("strArea"),
            "ingredients": ingredients,
            "instructions": meal.get("strInstructions", "")[:500],
            "data_found": True,
        }

    except Exception as e:
        return {"source": "TheMealDB", "error": str(e)}


#  2. Spoonacular 
def get_nutrition_from_spoonacular(food_name: str) -> dict:
    """
    Get detailed nutrition facts from Spoonacular.
    Requires SPOONACULAR_API_KEY in .env
    """
    try:
        if not SPOONACULAR_API_KEY:
            return {"source": "Spoonacular", "error": "Missing API key in .env"}

        search_url = (
            f"https://api.spoonacular.com/recipes/complexSearch"
            f"?query={food_name}&number=1&addRecipeNutrition=true&apiKey={SPOONACULAR_API_KEY}"
        )

        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return {"source": "Spoonacular", "food_name": food_name, "data_found": False}

        recipe = data["results"][0]
        nutrients = recipe.get("nutrition", {}).get("nutrients", [])

        nutrition_info = {}
        for item in nutrients:
            name = item["name"].lower().replace(" ", "_")
            nutrition_info[name] = {
                "amount": item.get("amount"),
                "unit": item.get("unit"),
            }

        return {
            "source": "Spoonacular",
            "food_name": recipe.get("title", food_name),
            "calories": nutrition_info.get("calories", {}).get("amount"),
            "protein_g": nutrition_info.get("protein", {}).get("amount"),
            "carbohydrates_g": nutrition_info.get("carbohydrates", {}).get("amount"),
            "fat_g": nutrition_info.get("fat", {}).get("amount"),
            "micronutrients": nutrition_info,
            "data_found": True,
        }

    except Exception as e:
        return {"source": "Spoonacular", "error": str(e)}
    


#  3. Combine Sources 
def combine_nutrition_sources(mealdb_data: dict, spoon_data: dict) -> dict:
    """
    Combine data from TheMealDB and Spoonacular.
    
    """
    combined = {}
    combined["food_name"] = (
        spoon_data.get("food_name") or mealdb_data.get("food_name") or "Unknown"
    )
    combined["sources"] = [s for s in [mealdb_data.get("source"), spoon_data.get("source")] if s]
    combined["category"] = mealdb_data.get("category")
    combined["area"] = mealdb_data.get("area")
    combined["ingredients"] = mealdb_data.get("ingredients", [])
    combined["instructions"] = mealdb_data.get("instructions", "")

    # Add nutrient values
    combined["calories_kcal"] = spoon_data.get("calories")
    combined["macronutrients"] = {
        "protein_g": spoon_data.get("protein_g"),
        "carbohydrates_g": spoon_data.get("carbohydrates_g"),
        "fat_g": spoon_data.get("fat_g"),
    }
    combined["micronutrients"] = spoon_data.get("micronutrients", {})

    return combined


# 4. Formatter 
def format_nutrition_output(food_name: str, data: dict) -> dict:
    """
    Final structured dictionary for LLM grounding.
    """
    return {
        "food_name": food_name,
        "source": data.get("sources", []),
        "category": data.get("category"),
        "area": data.get("area"),
        "calories": data.get("calories_kcal"),
        "macronutrients": data.get("macronutrients"),
        "micronutrients": data.get("micronutrients"),
        "ingredients": data.get("ingredients"),
        "serving_size_g": 100,
        "confidence": 0.9 if data.get("calories_kcal") else 0.6,
    }


#  Test Run 
if __name__ == "__main__":
    food = "Jollof Rice"
    print(json.dumps(get_nutrition_from_mealdb(food), indent=2))
    print(json.dumps(get_nutrition_from_spoonacular(food), indent=2))
