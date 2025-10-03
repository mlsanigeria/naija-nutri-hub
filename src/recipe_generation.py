import os
from openai import OpenAI
from typing import Dict

client = OpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT", "https://YOUR-RESOURCE-NAME.openai.azure.com/openai/v1/"),
)

def generate_recipe(dish_name: str) -> Dict:
    prompt = f"""
    Generate a detailed Nigerian recipe for {dish_name}.
    Include:
    - Short description
    - Ingredient list with measurements
    - Step-by-step cooking instructions
    - Approximate cooking time
    - Serving size
    """

    completion = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=[
            {"role": "system", "content": "You are a professional Nigerian chef."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    recipe_text = completion.choices[0].message.content

    return {
        "dish_name": dish_name.title(),
        "recipe": recipe_text
    }

