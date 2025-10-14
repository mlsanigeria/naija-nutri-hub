import os
import json
import yaml
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI
from tavily import TavilyClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ========================================
# Load environment variables and credentials
# ========================================
dotenv_path = Path(__file__).resolve().parents[2] / '.env'
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("AZURE_OPENAI_API_KEY")
base_url = os.getenv("AZURE_OPENAI_BASE_URL")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

if not all([api_key, base_url, deployment_name, api_version]):
    raise ValueError(
        "Missing Azure credentials. Please check .env file for: "
        "AZURE_OPENAI_API_KEY, AZURE_OPENAI_BASE_URL, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION"
    )

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=base_url,
    api_version=api_version
)

# ========================================
# Tavily Search Client
# ========================================
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    raise ValueError("Missing Tavily API key. Please set TAVILY_API_KEY in your .env file.")
tavily_client = TavilyClient(api_key=tavily_key)

# ========================================
# Load Local Dataset
# ========================================
DATA_PATH = "data/Nigerian Foods.csv"
if os.path.exists(DATA_PATH):
    food_df = pd.read_csv(DATA_PATH)
else:
    food_df = None


# ========================================
# Helper 1: TF-IDF Semantic Search (Local Dataset)
# ========================================
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------
# Helper: Search local dataset (TF-IDF version)
# --------------------------
# def search_local_dataset(food_name: str, top_k: int = 3):
#     if food_df is None or "Food_Name" not in food_df.columns:
#         return []

#     # ✅ Ensure columns exist
#     food_names = food_df["Food_Name"].astype(str).tolist()
#     descriptions = (
#         food_df["Description"].astype(str).tolist()
#         if "Description" in food_df.columns
#         else [""] * len(food_names)
#     )

#     # Combine food name + description for richer text search
#     combined_texts = [f"{n} {d}" for n, d in zip(food_names, descriptions)]

#     # Compute TF-IDF embeddings
#     vectorizer = TfidfVectorizer(stop_words="english")
#     tfidf_matrix = vectorizer.fit_transform(combined_texts)
#     query_vec = vectorizer.transform([food_name])

#     # Compute cosine similarity
#     similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
#     top_indices = similarities.argsort()[-top_k:][::-1]

#     # Return top matches
#     results = []
#     for idx in top_indices:
#         row = food_df.iloc[idx]
#         results.append({
#             "food": row.get("Food_Name", ""),
#             "ingredients": row.get("Ingredients", ""),
#             "instructions": row.get("Instructions", ""),
#             "similarity": float(similarities[idx]),
#         })
#     return results

def search_local_dataset(food_name: str, top_k: int = 3):
    if food_df is None or "Food_Name" not in food_df.columns:
        return []

    food_names = food_df["Food_Name"].astype(str).tolist()
    descriptions = (
        food_df["Description"].astype(str).tolist()
        if "Description" in food_df.columns
        else [""] * len(food_names)
    )
    combined_texts = [f"{n} {d}" for n, d in zip(food_names, descriptions)]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(combined_texts)
    query_vec = vectorizer.transform([food_name])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    for idx in top_indices:
        row = food_df.iloc[idx]
        results.append({
            "food": row.get("Food_Name", ""),
            "ingredients": row.get("Ingredients", ""),
            "instructions": row.get("Instructions", ""),
            "similarity": float(similarities[idx]),
        })
    return results




# ========================================
# Helper 2: Fetch from TheMealDB API
# ========================================
def get_recipe_from_mealdb(food_name: str):
    """
    Fetches recipe data from TheMealDB API by food name.
    """
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

with open("src/recipe-generation/recipe_prompt.yml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

# ========================================
# Helper 3: Tavily Web Search
# ========================================
def search_tavily(food_name: str):
    tavily_config = prompts.get("tavily", {})
    try:
        query = f"{food_name} recipe ingredients and preparation"
        results = tavily_client.search(
            query=query,
            max_results=tavily_config.get("max_results", 5),
            search_depth=tavily_config.get("search_depth", "basic"),
            include_domains=tavily_config.get("include_domains", []),
        )
        return [r["content"] for r in results.get("results", [])]
    except Exception:
        return []



# ========================================
# Main Recipe Generation Function
# ========================================
def generate_recipe(food_name: str):
    """
    Generates a recipe using combined sources:
    - Local Nigerian dataset (TF-IDF search)
    - TheMealDB API
    - Tavily web search
    Combines all info into a structured recipe using Azure OpenAI GPT-4o.
    """
    print(f"\n🔍 Searching for recipe: {food_name}")

    # Step 1: Local Dataset
    local_results = search_local_dataset(food_name)
    print(f"📘 Local dataset results found: {len(local_results)}")

    # Step 2: TheMealDB API
    mealdb_recipe = get_recipe_from_mealdb(food_name)
    print(f"🍴 TheMealDB recipe found: {mealdb_recipe is not None}")

    # Step 3: Tavily
    tavily_results = search_tavily(food_name)
    print(f"🌐 Tavily search results found: {len(tavily_results)}")

    # Combine for context
    combined_context = {
        "local_results": local_results,
        "mealdb_recipe": mealdb_recipe,
        "tavily_snippets": tavily_results,
    }

    # Step 4: Generate Structured Recipe via GPT
    
    system_prompt = prompts.get("recipe_generation_prompt", "")

    user_prompt_template = prompts.get("recipe_generation_prompt", "")
    user_prompt = user_prompt_template.format(
        food_name=food_name,
        context_data=json.dumps(combined_context, indent=2)
    )

    #user_prompt = f"Food name: {food_name}\n\nGrounded data:\n{json.dumps(combined_context, indent=2)}"

    try:
        response = client.chat.completions.create(
            model=deployment_name,  # use your Azure deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
        )

        recipe_json = json.loads(response.choices[0].message.content)
        recipe_json["source"] = "combined (local + TheMealDB + Tavily)"
        return recipe_json

    except Exception as e:
        print(f"❌ Error generating recipe: {e}")
        return None


