"""
nutrition_facts.py
------------------
Integrates the nutrition prompts, grounding tools, and Azure OpenAI model
to generate structured, accurate nutrition information.

Uses:
- nutrition_prompts.yml for LLM guidance
- nutrition_tools.py for grounded data from datasets/APIs
- Azure OpenAI (endpoint and key loaded from .env)
"""

import json
import yaml
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

from nutrition_tools import (
    get_nutrition_from_mealdb,
    get_nutrition_from_spoonacular,
    combine_nutrition_sources,
    format_nutrition_output,
)

# ========== Environment Setup ==========
load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_BASE_URL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version=AZURE_OPENAI_API_VERSION
)

import pathlib

def load_prompts(path: str = None) -> dict:
    """Safely load the nutrition prompt YAML relative to this script."""
    base_dir = pathlib.Path(__file__).parent
    prompt_path = path or base_dir / "nutrition_prompt.yml"
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    return prompts



# ========== Azure Model Call ==========
def generate_structured_nutrition(food_name: str, grounded_data: dict, prompts: dict) -> dict:
    """
    Generate structured nutrition output from Azure model.
    Combines LLM reasoning with grounded data for better accuracy.
    """
    base_prompt = prompts["nutrition_prompt"]
    instruction = base_prompt["grounding_prompt"]
    output_format = base_prompt["format_prompt"]

    user_prompt = (
        f"{instruction}\n"
        f"Food item: {food_name}\n\n"
        f"Grounded data:\n{json.dumps(grounded_data, indent=2)}\n\n"
        f"Output format example:\n{json.dumps(output_format, indent=2)}"
    )

    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "You are a nutrition expert that outputs structured JSON facts only."},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )

    message = response.choices[0].message.content
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        return {"error": "Model response could not be parsed as JSON", "raw": message}


#  Nutrition Facts Retrieval 
def get_structured_nutrition(food_name: str) -> dict:
    """
    Retrieve grounded nutrition facts and enrich them using Azure OpenAI.
    Returns structured JSON output.
    """
    # Load prompts
    prompts = load_prompts()

    # Step 1: Fetch from TheMealDB
    mealdb_data = get_nutrition_from_mealdb(food_name)

    # Step 2: Fetch from Spoonacular
    spoon_data = get_nutrition_from_spoonacular(food_name)

    # Step 3: Combine both sources
    grounded_data = combine_nutrition_sources(mealdb_data, spoon_data)

    # Step 4: Format base structure
    formatted_grounded = format_nutrition_output(food_name, grounded_data)

    # Step 5: Use Azure model for final enrichment/validation
    structured_result = generate_structured_nutrition(food_name, formatted_grounded, prompts)

    return structured_result


#  Testing 
if __name__ == "__main__":
    print("🔹 Azure OpenAI Nutrition Facts Generator")
    print("========================================\n")

    food = input("Enter a meal name: ").strip()

    print("\nFetching grounded nutrition data and generating structured output...\n")

    result = get_structured_nutrition(food)

    print("\n Structured Nutrition Facts:\n")
    print(json.dumps(result, indent=2))
