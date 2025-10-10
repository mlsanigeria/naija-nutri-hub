"""
recipe_tools.py
Contains helper functions for recipe generation:
- Search recipes in local dataset
- Fetch from TheMealDB API
- Fallback to model generation
"""

import os
import yaml
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
from pathlib import Path
from tavily import TavilyClient

def search_recipe_in_dataset(food_name: str, data_path: str):
    """
    Search the local Nigerian Foods CSV for a matching recipe description.
    Returns None if not found.
    """
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        return None

    with open(data_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if food_name.lower() in row["Food_Name"].lower():
                return {
                    "food_name": row["Food_Name"],
                    "description": row.get("Description", ""),
                    "main_ingredients": row.get("Main_Ingredients", ""),
                    "region": row.get("Region", ""),
                    "spice_level": row.get("Spice_Level", ""),
                }
    return None

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
