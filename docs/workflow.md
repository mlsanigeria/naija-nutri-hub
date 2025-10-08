🧩 API Workflow Documentation
📘 Overview

This workflow explainsthe Recipe Generation logic for naija-nutri-hub.
It intelligently generates Nigerian recipes by combining local data, third-party APIs, and AI model generation.
The pipeline ensures the best available recipe is returned, while minimizing API calls and maximizing contextual accuracy.

🔹 Step 1 — Local Dataset Lookup

Function: search_recipe_in_dataset(food_name, DATA_PATH)

Purpose: Quickly fetch recipes from Nigerian Foods.csv without making API calls.

Output: A dictionary containing recipe info like name, ingredients, and region.

If found:

{
  "source": "dataset",
  "data": {
    "food_name": "Jollof Rice",
    "description": "A delicious Nigerian dish made with rice, tomatoes, and spices.",
    "main_ingredients": "Rice, Tomato, Pepper, Onion",
    "region": "Nationwide",
    "spice_level": "Medium"
  }
}

🔹 Step 2 — TheMealDB API Fallback

Function: get_recipe_from_mealdb(food_name)

API Used: TheMealDB

Method: GET request to https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}

Purpose: Retrieve structured recipe details if the dataset doesn’t have it.

If found:

{
  "source": "themealdb_api",
  "data": { "title": "Jollof Rice", "ingredients": [...], "instructions": [...] }
}

🔹 Step 3 — AI Model Generation (Final Fallback)

If both the dataset and TheMealDB fail, the workflow dynamically generates a structured recipe using the OpenAI GPT model (e.g. gpt-4o-mini).

🧩 Prompt Construction

A YAML file (recipe_prompts.yml) defines the prompt template:

generate_recipe:
  prompt: |
    Create a detailed Nigerian recipe for {{ food_name }}.
    Description: {{ description }}
    Main Ingredients: {{ main_ingredients }}
    Region: {{ region }}
    Spice Level: {{ spice_level }}

    Return JSON with:
      - title
      - ingredients
      - instructions
      - nutrition_facts


The script fills placeholders using context from the dataset (if available):

filled_prompt = (
    template.replace("{{ food_name }}", context["food_name"])
            .replace("{{ description }}", context["description"])
            .replace("{{ main_ingredients }}", context["main_ingredients"])
            .replace("{{ region }}", context["region"])
            .replace("{{ spice_level }}", context["spice_level"])
)

🧠 Model Request
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful Nigerian chef assistant."},
        {"role": "user", "content": filled_prompt}
    ],
    response_format={"type": "json_object"}
)

✅ Output

The model returns a structured JSON:

{
  "source": "model",
  "data": {
    "title": "Jollof Rice",
    "ingredients": ["Rice", "Tomatoes", "Pepper", "Onion"],
    "instructions": ["Heat oil...", "Add tomatoes..."],
    "nutrition_facts": {"calories": 320}
  }
}

🖼️ Example Screenshots 
![alt text](image.png)
![alt text](image-1.png)
![alt text](image-2.png)