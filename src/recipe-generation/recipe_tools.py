# src/recipe-generation/recipe_tools.py (Final Version)

import os
import yaml
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path
from tavily import TavilyClient

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

# --- Initialize Tavily Search Client ---
tavily_key = os.getenv("TAVILY_API_KEY")

if not tavily_key:
    raise ValueError("Tavily API key not found. Please set TAVILY_API_KEY in your .env file.")

tavily_client = TavilyClient(api_key=tavily_key)

# --- Helper Function to Load the Prompt ---
def load_prompt_template():
    """Loads the recipe generation prompt from the YAML file."""
    prompt_file_path = Path(__file__).parent / "recipe_prompt.yml"
    with open(prompt_file_path, 'r') as f:
        prompt_data = yaml.safe_load(f)
    return prompt_data['recipe_generation_prompt']

# --- Main Grounded Recipe Generation Tool (Tavily Version) ---
def generate_recipe(food_name: str):
    """
    Generates a structured, grounded recipe by searching online with Tavily
    and then using Azure OpenAI to format and enhance the search results.
    """
    print(f"Starting grounded recipe generation for: {food_name}...")

    try:
        # --- Step 1: Search online for recipe content using Tavily ---
        print(f"Searching for '{food_name} recipe' with Tavily...")
        search_query = f"detailed recipe for {food_name}"
        
        # Using search_depth="advanced" gives more comprehensive results
        search_result = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            include_answer=True, # Ask Tavily to provide a summarized answer
            max_results=10 # Get the top 10 results for a richer context
        )
        
        # --- Step 2: Prepare the grounding context for the LLM ---
        # We will combine the summarized answer and the content of the top search results.
        context_data = search_result.get("answer", "") + "\n\n"
        for result in search_result.get("results", []):
            context_data += f"Source: {result.get('url')}\nContent: {result.get('content')}\n\n"
        
        if not context_data.strip():
            print(f"No content found for '{food_name}' via Tavily search.")
            return None

        print("Successfully prepared grounding context from Tavily search results.")

        # --- Step 3: Use Azure OpenAI to format the grounded data ---
        prompt_template = load_prompt_template()
        final_prompt = prompt_template.format(context_data=context_data)

        print(f"Sending request to Azure OpenAI using deployment: '{deployment_name}'...")
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": final_prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        
        recipe_json_string = response.choices[0].message.content
        print("Successfully received formatted response from Azure.")

        if recipe_json_string:
            return json.loads(recipe_json_string)
        else:
            print("Error: Received an empty response from the model.")
            return None

    except Exception as e:
        print(f"An unexpected error occurred during the recipe generation process: {e}")
        return None