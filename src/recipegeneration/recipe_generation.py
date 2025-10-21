# src/recipe-generation/recipe_generation.py

import json
from .recipe_tools import generate_recipe

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