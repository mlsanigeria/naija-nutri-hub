# src/recipe-generation/recipe_tools.py (Final Version)

import os
import yaml
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path

# --- Configuration (Final, Professional Version) ---
dotenv_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Get all required credentials from environment variables
api_key = os.getenv("AZURE_OPENAI_API_KEY")
base_url = os.getenv("AZURE_OPENAI_BASE_URL")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version = os.getenv("AZURE_OPENAI_API_VERSION") # <-- Loading the new version

# Check if all required environment variables are set
if not all([api_key, base_url, deployment_name, api_version]):
    raise ValueError(
        "Azure credentials not found. Please set all of the following in your .env file: "
        "AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION"
    )

# Initialize the Azure OpenAI client with all required parameters
client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=base_url,
    api_version=api_version # <-- Adding the required API version
)

# --- Helper Function to Load the Prompt ---
def load_prompt_template():
    """Loads the recipe generation prompt from the YAML file."""
    prompt_file_path = Path(__file__).parent / "recipe_prompt.yml"
    with open(prompt_file_path, 'r') as f:
        prompt_data = yaml.safe_load(f)
    return prompt_data['recipe_generation_prompt']

# --- Main Recipe Generation Tool ---
def generate_recipe(food_name: str):
    """
    Generates a structured recipe for a given food name using the configured Azure OpenAI deployment.
    """
    print(f"Starting recipe generation for: {food_name}...")
    try:
        prompt_template = load_prompt_template()
        final_prompt = prompt_template.format(food_name=food_name)

        print(f"Sending request to Azure OpenAI using deployment: '{deployment_name}'...")
        response = client.chat.completions.create(
            model=deployment_name, # This uses the deployment name from your .env file
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only returns valid JSON."},
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        recipe_json_string = response.choices[0].message.content
        print("Successfully received response from Azure.")

        if recipe_json_string:
            return json.loads(recipe_json_string)
        else:
            print("Error: Received an empty response from the model.")
            return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None