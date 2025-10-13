"""
recipe_tools.py
Contains helper functions for recipe generation:
- Search recipes in local dataset
- Fetch from TheMealDB API
- Fallback to model generation
"""
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
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import requests
import csv

load_dotenv()

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

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
)

# --- Initialize Tavily Search Client ---
tavily_key = os.getenv("TAVILY_API_KEY")

if not tavily_key:
    raise ValueError("Tavily API key not found. Please set TAVILY_API_KEY in your .env file.")

tavily_client = TavilyClient(api_key=tavily_key)

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load local dataset 
DATA_PATH = "data/Nigerian Foods.csv"
if os.path.exists(DATA_PATH):
    food_df = pd.read_csv(DATA_PATH)
else:
    food_df = None

def search_local_dataset(food_name: str, top_k: int = 3):
    if food_df is None:
        return []

    food_names = food_df["Food_Name"].astype(str).tolist()
    embeddings = model.encode(food_names, convert_to_tensor=True)
    query_embedding = model.encode(food_name, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, embeddings, top_k=top_k)[0]

    results = []
    for hit in hits:
        row = food_df.iloc[hit["corpus_id"]]
        results.append({
            "food": row.get("Food_Name", ""),
            "ingredients": row.get("Ingredients", ""),
            "instructions": row.get("Instructions", ""),
            "similarity": float(hit["score"]),
        })
    return results

def get_recipe_from_mealdb(food_name: str):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
    try:
        res = requests.get(url)
        if res.status_code == 200 and res.json().get("meals"):
            meal = res.json()["meals"][0]
            return {
                "title": meal.get("strMeal"),
                "category": meal.get("strCategory"),
                "area": meal.get("strArea"),
                "instructions": meal.get("strInstructions"),
                "ingredients": [
                    f"{meal.get(f'strIngredient{i}')} - {meal.get(f'strMeasure{i}')}"
                    for i in range(1, 21)
                    if meal.get(f"strIngredient{i}")
                ],
                "source": "TheMealDB",
            }
        return None
    except Exception:
        return None
    

def search_tavily(food_name: str):
    try:
        query = f"{food_name} recipe ingredients and preparation"
        results = tavily_client.search(query=query, max_results=5)
        return [r["content"] for r in results.get("results", [])]
    except Exception:
        return []


# --------------------------
# Main Recipe Generation Function
# --------------------------
def generate_recipe(food_name: str):
    """
    Generates a recipe by grounding data from:
    1. Local dataset
    2. TheMealDB API
    3. Tavily Search
    Then combines sources using Azure OpenAI GPT-4o.
    """
    print(f"\n🔍 Searching for recipe: {food_name}")

    # Step 1: Local dataset
    local_results = search_local_dataset(food_name)
    print(f"📘 Local dataset results found: {len(local_results)}")

    # Step 2: TheMealDB API
    mealdb_recipe = get_recipe_from_mealdb(food_name)
    print(f"🍴 TheMealDB recipe found: {mealdb_recipe is not None}")

    # Step 3: Tavily
    tavily_results = search_tavily(food_name)
    print(f"🌐 Tavily search results found: {len(tavily_results)}")

    # Combine data for context
    combined_context = {
        "local_results": local_results,
        "mealdb_recipe": mealdb_recipe,
        "tavily_snippets": tavily_results,
    }

    # Step 4: Generate final structured recipe with GPT-4o
    system_prompt = (
        "You are an expert African chef. Generate a detailed recipe JSON for the given food. "
        "Use available data to ensure cultural authenticity and realistic preparation steps. "
        "Include fields: title, region, category, ingredients, instructions, and estimated_time."
    )

    user_prompt = f"Food name: {food_name}\n\nGrounded data:\n{json.dumps(combined_context, indent=2)}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
        )
        recipe_json = json.loads(response.choices[0].message.content)
        recipe_json["source"] = "combined (local + API + Tavily)"
        return recipe_json

    except Exception as e:
        print(f" Error generating recipe: {e}")
        return None


