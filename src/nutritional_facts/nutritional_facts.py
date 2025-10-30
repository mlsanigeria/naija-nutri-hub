import json
import yaml
import os
import pathlib
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Optional, Dict, Any

from nutrition_tools import (
    get_nutrition_from_dataset,   
    get_nutrition_from_mealdb,
    get_nutrition_from_spoonacular,
    combine_nutrition_sources,
    format_nutrition_output,
)

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


def load_prompts(path: Optional[str] = None) -> dict:
    base_dir = pathlib.Path(__file__).parent
    prompt_path = path or base_dir / "nutrition_prompt.yml"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fill_placeholders(template: str, placeholders: Dict[str, str]) -> str:
    text = template
    for k, v in placeholders.items():
        text = text.replace("{{" + k + "}}", v if v is not None else "")
    return text


def generate_structured_nutrition(food_name: str, grounded_data: dict, prompts: dict, servings: float = 1, extra_inputs: Optional[Dict[str, Any]] = None):
    nutrition_prompt = prompts.get("nutrition_prompt", {})
    grounding_prompt = nutrition_prompt.get("grounding_prompt", "")
    format_prompt = nutrition_prompt.get("format_prompt", "")
    validation_prompt = nutrition_prompt.get("validation_prompt", "")

    placeholders = {
        "food_name": food_name,
        "serving_description": grounded_data.get("portion_size") or f"{servings} serving{'s' if servings > 1 else ''}",
        "servings": str(int(servings)),
        "retrieved_dataset_context": grounded_data.get("retrieved_dataset_context") or "",
        "api_context": grounded_data.get("api_context") or "",
        "inferred_context": grounded_data.get("inferred_context") or "",
    }

    user_prompt = (
        fill_placeholders(grounding_prompt, placeholders)
        + "\n\n"
        + fill_placeholders(format_prompt, placeholders)
        + "\n\nValidation requirements:\n"
        + fill_placeholders(validation_prompt, placeholders)
    )

    try:
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a nutrition analyst that must strictly follow the JSON schema."},
                {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "nutrition_schema",
                "schema": {
                    "type": "object",
                    "properties": {
                        "food_name": {"type": "string"},
                        "servings": {"type": "integer"},
                        "portion_size": {"type": "string"},
                        "nutrition_facts": {
                            "type": "object",
                            "properties": {
                                "calories": {"type": ["number", "null"]},
                                "protein_g": {"type": ["number", "null"]},
                                "fat_g": {"type": ["number", "null"]},
                                "carbohydrates_g": {"type": ["number", "null"]},
                                "fiber_g": {"type": ["number", "null"]},
                                "sugar_g": {"type": ["number", "null"]},
                                "cholesterol_mg": {"type": ["number", "null"]},
                                "sodium_mg": {"type": ["number", "null"]}
                            },
                            "required": ["calories", "protein_g", "fat_g", "carbohydrates_g"]
                        },
                        "sources": {
                            "type": "object",
                            "properties": {
                                "dataset": {"type": "boolean"},
                                "mealdb": {"type": "boolean"},
                                "spoonacular": {"type": "boolean"}
                            }
                        },
                        "metadata": {"type": "object"}
                    },
                    "required": ["food_name","servings", "nutrition_facts", "sources"]
                }
            }
        },
    )


        message = response.choices[0].message.content
        return json.loads(message)
    except Exception as e:
        return {"error": "Could not parse model output as JSON", "exception": str(e)}


def get_structured_nutrition(food_name: str, servings: float = 1, extra_inputs: Optional[Dict[str, Any]] = None, dataset_path: str = "data/Nigerian Foods.csv"):
    prompts = load_prompts()
    
    
    dataset_data = get_nutrition_from_dataset(food_name, dataset_path=dataset_path)
    mealdb_data = get_nutrition_from_mealdb(food_name)
    spoon_data = get_nutrition_from_spoonacular(food_name)

    grounded = combine_nutrition_sources(
        dataset_data,
        mealdb_data,
        spoon_data,
        serving_description=f"{servings} serving{'s' if servings>1 else ''}",
        extra_inputs=extra_inputs
    )

    formatted_grounded = format_nutrition_output(grounded)

    structured = generate_structured_nutrition(
        food_name,
        formatted_grounded,
        prompts,
        servings=servings,
        extra_inputs=extra_inputs
    )

    return structured


if __name__ == "__main__":
    print("🍲 Nutrition Facts Generator")
    food = input("Enter food name (e.g. Efo Riro): ").strip()
    servings_input = input("Enter number of servings (default=1): ").strip()
    try:
        servings = float(servings_input) if servings_input else 1
    except ValueError:
        servings = 1
    extra = input("Extra context (region/style) or Enter: ").strip()
    extra_inputs = {"context": extra} if extra else None

    result = get_structured_nutrition(food, servings=servings, extra_inputs=extra_inputs)
    print(json.dumps(result, indent=2))





