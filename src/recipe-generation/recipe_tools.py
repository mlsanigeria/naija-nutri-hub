"""
recipe_tools.py
Contains helper functions for recipe generation:
- Search recipes in local dataset
- Fetch from TheMealDB API
- Fallback to model generation
"""

import os
import csv
import requests

def search_recipe_in_dataset(food_name: str, data_path: str):
    """
    Search the local Nigerian Foods CSV for a matching recipe description.
    Returns None if not found.
    """
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        return None

    with open(data_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if food_name.lower() in row["Food_Name"].lower():
                return {
                    "food_name": row["Food_Name"],
                    "description": row.get("Description", ""),
                    "main_ingredients": row.get("Main_Ingredients", ""),
                    "region": row.get("Region", ""),
                    "spice_level": row.get("Spice_Level", ""),
                }
    return None


def get_recipe_from_mealdb(food_name: str):
    """
    Fetch recipe data from TheMealDB API.
    Returns structured recipe if found, else None.
    """
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data or not data.get("meals"):
            return None

        meal = data["meals"][0]
        ingredients = []
        for i in range(1, 21):
            name = meal.get(f"strIngredient{i}")
            qty = meal.get(f"strMeasure{i}")
            if name and name.strip():
                ingredients.append({"name": name.strip(), "quantity": qty.strip()})

        return {
            "food_name": meal.get("strMeal"),
            "ingredients": ingredients,
            "steps": meal.get("strInstructions", "").split("\r\n"),
            "serving_size": "N/A",
            "estimated_time": "N/A",
        }
    except Exception as e:
        print(f"Error fetching recipe from TheMealDB: {e}")
        return None
