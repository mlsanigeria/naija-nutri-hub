<<<<<<< HEAD
"""
recipe_generation.py
Main logic for recipe generation:
- Attempts to get recipe from dataset
- Falls back to TheMealDB
- Else generates with model using structured prompt
"""

import os
import yaml
from openai import AzureOpenAI
from recipe_tools import search_recipe_in_dataset, get_recipe_from_mealdb



DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/Nigerian Foods.csv")

# Initialize Azure OpenAI client

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="",
    api_key="",
)

def generate_structured_recipe(food_name: str):
    """
    Generates a structured recipe for a given food item.
    Priority:
      1. Try local dataset (context)
      2. Try TheMealDB API
      3. Generate using model with YAML prompt (grounded with dataset context)
    """

    # local dataset
    dataset_recipe = search_recipe_in_dataset(food_name, DATA_PATH)
    if dataset_recipe:
        
        context = {
            "food_name": dataset_recipe.get("food_name", food_name),
            "description": dataset_recipe.get("description", "A delicious Nigerian dish."),
            "main_ingredients": dataset_recipe.get("main_ingredients", ""),
            "region": dataset_recipe.get("region", "Nationwide"),
            "spice_level": dataset_recipe.get("spice_level", "Medium"),
        }
    else:
        # fallback context
        context = {
            "food_name": food_name,
            "description": "",
            "main_ingredients": "",
            "region": "",
            "spice_level": "",
        }

    # TheMealDB API 
    api_recipe = get_recipe_from_mealdb(food_name)
    if api_recipe:
        return {
            "source": "themealdb_api",
            "data": api_recipe
        }

    # Generate with model (YAML-based prompt)
    prompt_file = os.path.join(os.path.dirname(__file__), "recipe_prompt.yml")
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    
    template = prompts["prompt"]

    filled_prompt = (
        template.replace("{{ food_name }}", context["food_name"])
                .replace("{{ description }}", context["description"])
                .replace("{{ main_ingredients }}", context["main_ingredients"])
                .replace("{{ region }}", context["region"])
                .replace("{{ spice_level }}", context["spice_level"])
    )

    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian chef assistant."},
                {"role": "user", "content": filled_prompt}
            ],
            response_format={"type": "json_object"}
        )

        structured_recipe = completion.choices[0].message.content
        return {
            "source": "model",
            "data": structured_recipe
        }

    except Exception as e:
        return {
            "source": "error",
            "error": str(e),
            "context_used": context
        }


# Quick test
if __name__ == "__main__":
    result = generate_structured_recipe("Jollof Rice")
    print(result)
=======
# src/recipe-generation/recipe_generation.py

import json
from recipe_tools import generate_recipe

def get_recipe_for_dish(food_name: str):
    """
    A simple function to demonstrate how to use the recipe generation tool.
    
    Args:
        food_name (str): The name of the dish to get a recipe for.
        
    Returns:
        dict or None: The recipe data if successful, otherwise None.
    """
    print(f"Requesting recipe for: {food_name}")
    recipe_data = generate_recipe(food_name)
    
    if recipe_data:
        print("\n--- Successfully Generated Recipe ---")
        print(json.dumps(recipe_data, indent=2))
        return recipe_data
    else:
        print(f"\n--- Failed to Generate Recipe for {food_name} ---")
        return None

# This part allows the script to be run as an example from the command line
if __name__ == "__main__":
    # You can change this to test other dishes
    dish_to_try = "Jollof Rice" 
    get_recipe_for_dish(dish_to_try)
>>>>>>> upstream/main
