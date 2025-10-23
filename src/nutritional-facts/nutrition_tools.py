""""
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
from typing import Optional

load_dotenv()

# Load API key
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


#  Get metadata and ingredients from TheMealDB
def get_nutrition_from_mealdb(food_name: str) -> dict:
    """Fetch basic metadata (category, area, ingredients) from TheMealDB."""
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("meals"):
            return {"source": "TheMealDB", "data_found": False}

        meal = data["meals"][0]
        ingredients = [
            {
                "ingredient": meal.get(f"strIngredient{i}"),
                "measure": meal.get(f"strMeasure{i}")
            }
            for i in range(1, 21)
            if meal.get(f"strIngredient{i}")
        ]

        main_ingredient = ingredients[0]["ingredient"] if ingredients else None

        return {
            "source": "TheMealDB",
            "food_name": meal.get("strMeal", food_name),
            "category": meal.get("strCategory"),
            "area": meal.get("strArea"),
            "origin": meal.get("strArea") or "Unknown",
            "main_ingredient": main_ingredient,
            "ingredients": ingredients,
            "instructions": (meal.get("strInstructions") or "")[:500],
            "data_found": True,
        }

    except Exception as e:
        return {"source": "TheMealDB", "error": str(e), "data_found": False}


# Get nutrition details from Spoonacular
def get_nutrition_from_spoonacular(food_name: str) -> dict:
    """Fetch detailed nutrition info from Spoonacular API."""
    try:
        if not SPOONACULAR_API_KEY:
            return {"source": "Spoonacular", "error": "Missing API key", "data_found": False}

        url = (
            f"https://api.spoonacular.com/recipes/complexSearch"
            f"?query={food_name}&number=1&addRecipeNutrition=true&apiKey={SPOONACULAR_API_KEY}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            return {"source": "Spoonacular", "data_found": False}

        recipe = data["results"][0]
        nutrients = recipe.get("nutrition", {}).get("nutrients", [])

        def get_value(name):
            for n in nutrients:
                if n["name"].lower() == name.lower():
                    return n["amount"]
            return None

        return {
            "source": "Spoonacular",
            "food_name": recipe.get("title", food_name),
            "calories": get_value("Calories"),
            "protein_g": get_value("Protein"),
            "fat_g": get_value("Fat"),
            "carbohydrates_g": get_value("Carbohydrates"),
            "fiber_g": get_value("Fiber"),
            "sugar_g": get_value("Sugar"),
            "cholesterol_mg": get_value("Cholesterol"),
            "sodium_mg": get_value("Sodium"),
            "data_found": True,
        }

    except Exception as e:
        return {"source": "Spoonacular", "error": str(e), "data_found": False}


# Combine results
def combine_nutrition_sources(
    mealdb_data: dict,
    spoon_data: dict,
    dataset_data: Optional[dict] = None,
    serving_size_g: float = 100.0
) -> dict:
    """Combine data from dataset + APIs and adjust for serving size."""

    # Detect which sources returned data
    has_dataset = bool(dataset_data and any(dataset_data.values()))
    has_mealdb = mealdb_data.get("data_found", False)
    has_spoon = spoon_data.get("data_found", False)

    # Decide base food name (in priority order)
    food_name = (
        (dataset_data or {}).get("food_name")
        or spoon_data.get("food_name")
        or mealdb_data.get("food_name")
    )

    combined = {
        "food_name": food_name,
        "sources": {
            "dataset": has_dataset,
            "mealdb": has_mealdb,
            "spoonacular": has_spoon,
        },
    }

    
    #  Merge metadata
    
    combined["metadata"] = {
        "category": (
            (dataset_data or {}).get("category")
            or mealdb_data.get("category")
            or "Unknown"
        ),
        "area": (
            (dataset_data or {}).get("area")
            or mealdb_data.get("area")
            or "Unknown"
        ),
        "origin": (
            (dataset_data or {}).get("origin")
            or mealdb_data.get("origin")
            or "Unknown"
        ),
        "main_ingredient": (
            (dataset_data or {}).get("main_ingredient")
            or mealdb_data.get("main_ingredient")
            or "Unknown"
        ),
        "dietary_tags": infer_dietary_tags(
            (dataset_data or {}).get("ingredients", [])
            or mealdb_data.get("ingredients", [])
        ),
    }

    
    #  Nutrient scaling
   
    scale_factor = serving_size_g / 100.0

    def scale(value):
        return round(value * scale_factor, 2) if isinstance(value, (int, float)) else None

    # Merge nutrients (dataset preferred > spoon > mealdb)
    combined["nutrition_facts"] = {
        "calories": scale(
            (dataset_data or {}).get("calories")
            or spoon_data.get("calories")
            or mealdb_data.get("calories")
        ),
        "protein_g": scale(
            (dataset_data or {}).get("protein_g")
            or spoon_data.get("protein_g")
            or mealdb_data.get("protein_g")
        ),
        "fat_g": scale(
            (dataset_data or {}).get("fat_g")
            or spoon_data.get("fat_g")
            or mealdb_data.get("fat_g")
        ),
        "carbohydrates_g": scale(
            (dataset_data or {}).get("carbohydrates_g")
            or spoon_data.get("carbohydrates_g")
            or mealdb_data.get("carbohydrates_g")
        ),
        "fiber_g": scale(
            (dataset_data or {}).get("fiber_g")
            or spoon_data.get("fiber_g")
            or mealdb_data.get("fiber_g")
        ),
        "sugar_g": scale(
            (dataset_data or {}).get("sugar_g")
            or spoon_data.get("sugar_g")
            or mealdb_data.get("sugar_g")
        ),
        "cholesterol_mg": scale(
            (dataset_data or {}).get("cholesterol_mg")
            or spoon_data.get("cholesterol_mg")
            or mealdb_data.get("cholesterol_mg")
        ),
        "sodium_mg": scale(
            (dataset_data or {}).get("sodium_mg")
            or spoon_data.get("sodium_mg")
            or mealdb_data.get("sodium_mg")
        ),
    }

    combined["serving_size_g"] = serving_size_g
    return combined



# infer dietary tags
def infer_dietary_tags(ingredients):
    """Basic heuristic to infer dietary categories."""
    text = " ".join([i.get("ingredient", "").lower() for i in ingredients])
    tags = []

    if not any(x in text for x in ["beef", "chicken", "pork", "fish", "goat"]):
        tags.append("Vegetarian")
    if not any(x in text for x in ["milk", "butter", "cheese", "yogurt"]):
        tags.append("Lactose intolerant")
    if not any(x in text for x in ["flour", "wheat", "barley"]):
        tags.append("Gluten-free")
    tags.append("Halal")

    return tags


# Output formatter
def format_nutrition_output(food_name: str, data: dict) -> dict:
    """Return clean structured JSON."""
    return {
        "food_name": food_name,
        "serving_size_g": data.get("serving_size_g", 100),
        "nutrition_facts": data.get("nutrition_facts", {}),
        "sources": data.get("sources", {}),
        "metadata": data.get("metadata", {}),
    }


# Test run
if __name__ == "__main__":
    food = "Pancakes"
    mealdb = get_nutrition_from_mealdb(food)
    spoon = get_nutrition_from_spoonacular(food)
    combined = combine_nutrition_sources(mealdb, spoon, serving_size_g=200)
    print(json.dumps(format_nutrition_output(food, combined), indent=2))

