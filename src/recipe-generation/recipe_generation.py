import os
import yaml
from openai import AzureOpenAI
from recipe_tools import search_recipe_in_dataset, get_recipe_from_mealdb

# Initialize OpenAI client

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="",
    api_key="",
)

# Path to your dataset (optional, if available)
DATA_PATH = os.path.join(os.path.dirname(__file__), "Nigerian Foods.csv")

def generate_structured_recipe(food_name: str):
    """
    Generates a structured recipe for a given food item.
    Priority:
      1. Try local dataset (context)
      2. Try TheMealDB API
      3. Generate using model with YAML prompt (grounded with dataset context)
    """

    print(f"Starting recipe generation for: {food_name}\n")

    # STEP 1: Try local dataset
    print("🔍 Step 1: Searching local dataset...")
    dataset_recipe = search_recipe_in_dataset(food_name, DATA_PATH)

    if dataset_recipe:
        print("Recipe found in dataset! Adding context...\n")
        context = {
            "food_name": dataset_recipe.get("food_name", food_name),
            "description": dataset_recipe.get("description", "A delicious Nigerian dish."),
            "main_ingredients": dataset_recipe.get("main_ingredients", ""),
            "region": dataset_recipe.get("region", "Nationwide"),
            "spice_level": dataset_recipe.get("spice_level", "Medium"),
        }
    else:
        print(" No entry found in dataset. Proceeding with fallback context.\n")
        context = {
            "food_name": food_name,
            "description": "",
            "main_ingredients": "",
            "region": "",
            "spice_level": "",
        }

    # STEP 2: Try TheMealDB API
    print("🌐 Step 2: Fetching from TheMealDB API...")
    api_recipe = get_recipe_from_mealdb(food_name)
    if api_recipe:
        print(" Recipe fetched from TheMealDB API!\n")
        return {
            "source": "themealdb_api",
            "data": api_recipe
        }

    # STEP 3: Generate with model (YAML-based prompt)
    print("🤖 Step 3: Generating recipe using model (Azure OpenAI)...\n")
    prompt_file = os.path.join(os.path.dirname(__file__), "recipe_prompt.yml")
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    template = prompts["prompt"]

    # Fill placeholders with dataset context
    filled_prompt = (
        template.replace("{{ food_name }}", context["food_name"])
                .replace("{{ description }}", context["description"])
                .replace("{{ main_ingredients }}", context["main_ingredients"])
                .replace("{{ region }}", context["region"])
                .replace("{{ spice_level }}", context["spice_level"])
    )

    print(" Prompt being sent to model:\n")
    print(filled_prompt, "\n") 

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian chef assistant."},
                {"role": "user", "content": filled_prompt}
            ],
            response_format={"type": "json_object"}
        )

        structured_recipe = completion.choices[0].message.content
        print("Model responded with structured recipe!\n")  
        return {
            "source": "model",
            "data": structured_recipe
        }

    except Exception as e:
        print(" Error occurred during model generation!\n")
        print("Error message:", str(e))
        return {
            "source": "error",
            "error": str(e),
            "context_used": context
        }


# 🚀 Quick test
if __name__ == "__main__":
    result = generate_structured_recipe("Jollof Rice")

    print(result)

