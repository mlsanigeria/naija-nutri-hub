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
from typing import Optional

load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


#  Fetch from TheMealDB 
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


# Fetch from Spoonacular 
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


# -Origin Mapper 
def infer_origin(food_name: str, default_origin: str = "Unknown") -> str:
    """Infer origin for local foods (fallback for API defaults)."""
    name = food_name.lower()
    mapping = {
        "jollof": "West Africa",
        "efo riro": "Yoruba (Nigeria)",
        "ofe nsala": "Igbo (Nigeria)",
        "moi moi": "Yoruba (Nigeria)",
        "akara": "Yoruba (Nigeria)",
        "egusi": "Nigeria (Various Tribes)",
        "suya": "Hausa (Nigeria)",
        "tuwo": "Hausa (Nigeria)",
        "rice and beans": "Nigeria (General)",
    }
    for key, val in mapping.items():
        if key in name:
            return val
    return default_origin


# Dietary Tag Heuristics 
def infer_dietary_tags(ingredients):
    """Infer dietary tags from ingredients list."""
    text = " ".join([i.get("ingredient", "").lower() for i in ingredients])
    tags = []

    # Vegetarian
    if not any(x in text for x in ["beef", "chicken", "pork", "fish", "goat"]):
        tags.append("Vegetarian")

    # Lactose tolerance (corrected)
    if any(x in text for x in ["milk", "butter", "cheese", "yogurt"]):
        tags.append("Lactose tolerant")
    else:
        tags.append("Lactose-free")

    # Gluten-free
    if not any(x in text for x in ["flour", "wheat", "barley"]):
        tags.append("Gluten-free")

    # Default halal
    tags.append("Halal")

    return tags


# Combine Sources 
def combine_nutrition_sources(
    mealdb_data: dict,
    spoon_data: dict,
    dataset_data: Optional[dict] = None,
    serving_size_g: Optional[float] = None,
    extra_inputs: Optional[dict] = None
) -> dict:
    """Combine data from dataset + APIs and adjust for serving size."""
    # Default to 100g only if serving size wasn't passed
    serving_size_g = float(serving_size_g) if serving_size_g else 100.0

    # Detect data sources
    has_dataset = bool(dataset_data and any(dataset_data.values()))
    has_mealdb = mealdb_data.get("data_found", False)
    has_spoon = spoon_data.get("data_found", False)

    # Get food name safely
    food_name = (
        (dataset_data or {}).get("food_name")
        or spoon_data.get("food_name")
        or mealdb_data.get("food_name")
        or "Unknown Food"
    )

    combined = {
        "food_name": food_name,
        "sources": {
            "dataset": has_dataset,
            "mealdb": has_mealdb,
            "spoonacular": has_spoon,
        },
    }

    # Merge metadata 
    combined["metadata"] = {
        "category": (dataset_data or {}).get("category") or mealdb_data.get("category") or "Unknown",
        "area": (dataset_data or {}).get("area") or mealdb_data.get("area") or "Unknown",
        "origin": infer_origin(
            food_name,
            (dataset_data or {}).get("origin") or mealdb_data.get("origin") or "Unknown",
        ),
        "main_ingredient": (dataset_data or {}).get("main_ingredient")
        or mealdb_data.get("main_ingredient")
        or "Unknown",
        "dietary_tags": infer_dietary_tags(
            (dataset_data or {}).get("ingredients", [])
            or mealdb_data.get("ingredients", [])
        ),
        "extra_inputs": extra_inputs or {},
    }

    
    scale_factor = serving_size_g / (dataset_data.get("serving_size_g", 100.0) if dataset_data else 100.0)

    def scale(value):
        return round(value * scale_factor, 2) if isinstance(value, (int, float)) else None

    combined["nutrition_facts"] = {
        k: scale(
            (dataset_data or {}).get(k)
            or spoon_data.get(k)
            or mealdb_data.get(k)
        )
        for k in [
            "calories",
            "protein_g",
            "fat_g",
            "carbohydrates_g",
            "fiber_g",
            "sugar_g",
            "cholesterol_mg",
            "sodium_mg",
        ]
    }

    combined["serving_size_g"] = serving_size_g
    return combined

#  Formatter 
def format_nutrition_output(food_name: str, data: dict) -> dict:
    """Return clean structured JSON."""
    return {
        "food_name": food_name,
        "serving_size_g": data.get("serving_size_g", 100),
        "nutrition_facts": data.get("nutrition_facts", {}),
        "sources": data.get("sources", {}),
        "metadata": data.get("metadata", {}),
    }


# ---------------------- 7️⃣ Test Run ----------------------
if __name__ == "__main__":
    food = "Efo Riro"
    mealdb = get_nutrition_from_mealdb(food)
    spoon = get_nutrition_from_spoonacular(food)
    combined = combine_nutrition_sources(mealdb, spoon, serving_size_g=200, extra_inputs={"style": "Yoruba"})
    print(json.dumps(format_nutrition_output(food, combined), indent=2))


