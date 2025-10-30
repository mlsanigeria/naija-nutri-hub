# src/recipe-generation/recipe_generation.py

import json
from typing import Optional, List
from .recipe_tools import generate_recipe

def get_recipe_for_dish(
    food_name: str,
    servings: Optional[float] = None,
    dietary_restriction: Optional[List[str]] = None,
    extra_inputs: Optional[str] = None
):
    """
    Generate a recipe for a dish with optional parameters.
    
    Args:
        food_name (str): The name of the dish to get a recipe for.
        servings (Optional[float]): Number of servings/portions (e.g., 3, 4).
        dietary_restriction (Optional[List[str]]): List of dietary restrictions 
            (e.g., ["Vegetarian", "Vegan", "Lactose intolerant", "Gluten-free", 
             "Nut allergy", "Diabetic", "Halal"]).
        extra_inputs (Optional[str]): Additional context or preferences 
            (e.g., "Preferred Cuisine: Yoruba").
        
    Returns:
        dict or None: The recipe data if successful, otherwise None.
    """
    print(f"Requesting recipe for: {food_name}")
    if servings:
        print(f"  - Servings: {servings}")
    if dietary_restriction:
        print(f"  - Dietary Restrictions: {', '.join(dietary_restriction)}")
    if extra_inputs:
        print(f"  - Extra Inputs: {extra_inputs}")
    
    recipe_data = generate_recipe(
        food_name=food_name,
        servings=servings,
        dietary_restriction=dietary_restriction,
        extra_inputs=extra_inputs
    )
    
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