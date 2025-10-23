"""
nutrition_facts.py
------------------
Integrates the nutrition prompts, grounding tools, and Azure OpenAI model
to generate structured, accurate nutrition information.

Uses:
- nutrition_prompt.yml for LLM guidance
- nutrition_tools.py for grounded data from datasets/APIs
- Azure OpenAI (endpoint and key loaded from .env)
"""

import json
import yaml
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import pathlib
from typing import Optional

from nutrition_tools import (
    get_nutrition_from_mealdb,
    get_nutrition_from_spoonacular,
    combine_nutrition_sources,
    format_nutrition_output,
)


# Environment Setup

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_BASE_URL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION,
)



# Prompt Loader

def load_prompts(path: Optional[str] = None) -> dict:
    """Safely load nutrition prompt YAML relative to this script."""
    base_dir = pathlib.Path(__file__).parent
    prompt_path = path or base_dir / "nutrition_prompt.yml"

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    return prompts



# Azure OpenAI Call

def generate_structured_nutrition(
    food_name: str,
    grounded_data: dict,
    prompts: dict,
    servings: int = 1,
) -> dict:
    """
    Generate structured nutrition output from Azure model.
    Combines LLM reasoning with grounded data for better accuracy.
    """
    base_prompt = prompts["nutrition_prompt"]
    instruction = base_prompt.get("grounding_prompt", "")
    output_format = base_prompt.get("format_prompt", {})

    user_prompt = (
        f"{instruction}\n\n"
        f"Food item: {food_name}\n"
        f"Number of servings: {servings}\n"
        f"Serving size (g): {grounded_data.get('serving_size_g', 100)}\n\n"
        f"Grounded nutrition data:\n{json.dumps(grounded_data, indent=2)}\n\n"
        f"Enrich only missing or null values (e.g., calories, fat, origin, tags) using reasoning. "
        f"Do NOT rescale numbers, they are already per serving.\n"
        f"Ensure the JSON matches this format:\n{json.dumps(output_format, indent=2)}"
    )

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a nutrition expert that outputs structured JSON only."},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        message = response.choices[0].message.content
        return json.loads(message)

    except json.JSONDecodeError:
        return {"error": "Model response could not be parsed as JSON", "raw": message}
    except Exception as e:
        return {"error": str(e)}



# Nutrition Facts Retrieval

def get_structured_nutrition(food_name: str, servings: int = 1) -> dict:
    """
    Retrieve grounded nutrition facts and enrich them using Azure OpenAI.
    Returns structured JSON output aligned with schema expectations.
    """

    # 1. Load prompts
    prompts = load_prompts()

    # 2. Get data from TheMealDB and Spoonacular
    mealdb_data = get_nutrition_from_mealdb(food_name)
    spoon_data = get_nutrition_from_spoonacular(food_name)

    # 3. Combine grounded sources
    grounded_data = combine_nutrition_sources(mealdb_data, spoon_data, serving_size_g=100 * servings)

    # 4. Format base structure
    formatted_grounded = format_nutrition_output(food_name, grounded_data)

    # 5. Enrich with Azure model
    structured_result = generate_structured_nutrition(food_name, formatted_grounded, prompts, servings)

    return structured_result



#  Testing

if __name__ == "__main__":
    print("🔹 Azure OpenAI Nutrition Facts Generator")
    print("========================================\n")

    food = input("Enter a meal name: ").strip()
    servings_input = input("Enter number of portions (default 1): ").strip()
    servings = int(servings_input) if servings_input.isdigit() else 1

    print("\nFetching grounded nutrition data and generating structured output...\n")

    result = get_structured_nutrition(food, servings)

    print("\n Structured Nutrition Facts:\n")
    print(json.dumps(result, indent=2))
