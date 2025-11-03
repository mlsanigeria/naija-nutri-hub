import os
import json
import yaml
import requests
import pandas as pd
from pathlib import Path
from typing import Optional
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
dalle_deployment_name = os.getenv("AZURE_OPENAI_DALL_E_DEPLOYMENT_NAME")

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

# --- Helper Function to Load the Prompt ---
def load_prompt_template():
    """Loads the recipe generation prompt from the YAML file."""
    prompt_file_path = Path(__file__).parent / "recipe_prompt.yml"
    with open(prompt_file_path, 'r', encoding="utf-8") as f:
        prompt_data = yaml.safe_load(f)
    return prompt_data
    
prompts = load_prompt_template()

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
# Helper 4: Azure OpenAI DALL-E 3 Image Generation
# ========================================

def generate_step_image(step_description: str, food_name: str) -> str | None:
    """
    Generates an image using Azure OpenAI DALL-E 3 and returns the image URL.
    """
    image_prompt = (
        f"A clear, high-quality, top-down photograph of a cooking step. "
        f"The focus is on '{step_description}' for a recipe of '{food_name}'. "
        f"Use a simple, clean kitchen background. The image must not contain any text, logos, or brand names."
    )
    
    try:
        print(f"🖼️ Generating image for step: '{step_description[:50]}...'")
        result = client.images.generate(
            model=dalle_deployment_name, # Use the DALL-E 3 deployment name
            prompt=image_prompt,
            n=1,
            size="1024x1024", 
            style="vivid" 
        )
        
        if result.data and result.data[0].url:
            print("✅ Image URL generated successfully.")
            return result.data[0].url
        else:
            print("⚠️ Image generation succeeded but no URL was found in the response.")
            return None
            
    except Exception as e:
        print(f"❌ Error generating image for step '{step_description[:50]}...': {e}")
        return None

# ========================================
# Main Recipe Generation Function
# ========================================
def generate_recipe(
    food_name: str,
    servings: Optional[float] = None,
    dietary_restriction: Optional[list] = None,
    extra_inputs: Optional[str] = None
):
    """
    Generates a recipe using combined sources:
    - Local Nigerian dataset (TF-IDF search)
    - TheMealDB API
    - Tavily web search
    Combines all info into a structured recipe using Azure OpenAI GPT-4o.
    
    Args:
        food_name (str): The name of the dish to generate a recipe for.
        servings (Optional[float]): Desired number of servings/portions.
        dietary_restriction (Optional[list]): List of dietary restrictions to consider
            (e.g., ["Vegetarian", "Vegan", "Lactose intolerant", "Gluten-free", 
             "Nut allergy", "Diabetic", "Halal"]).
        extra_inputs (Optional[str]): Additional user preferences or context 
            (e.g., "Preferred Cuisine: Yoruba").
    
    Returns:
        dict: The generated recipe JSON with all structured data.
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
    
    # Build user preferences string for the prompt
    user_preferences_parts = []
    if servings:
        user_preferences_parts.append(f"- Desired servings: {servings} portions/plates")
    if dietary_restriction:
        user_preferences_parts.append(f"- Dietary restrictions: {', '.join(dietary_restriction)}")
    if extra_inputs:
        user_preferences_parts.append(f"- Additional preferences: {extra_inputs}")
    
    if not user_preferences_parts:
        user_preferences_str = "No specific user preferences provided."
    else:
        user_preferences_str = "\n".join(user_preferences_parts)

    # Step 4: Generate Structured Recipe via GPT
    
    system_prompt = prompts.get("recipe_generation_prompt", "")

    user_prompt_template = prompts.get("recipe_generation_prompt", "")
    user_prompt = user_prompt_template.format(
        food_name=food_name,
        user_preferences=user_preferences_str,
        context_data=json.dumps(combined_context, indent=2)
    )

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
        
        # Add user preferences metadata to the recipe
        if servings:
            recipe_json["servings"] = servings
        if dietary_restriction:
            recipe_json["dietary_restrictions"] = dietary_restriction
        if extra_inputs:
            recipe_json["user_preferences"] = extra_inputs
        
        # === NEW LOGIC: Generate Images for Each Recipe Step ===
        if "steps" in recipe_json and isinstance(recipe_json["steps"], list):
            print("\n📸 Starting image generation for recipe steps...")
            recipe_food_name = recipe_json.get("title", food_name)
            
            for i, step in enumerate(recipe_json["steps"]):
                if "instruction" in step:
                    step_description = step["instruction"]
                    image_url = generate_step_image(step_description, recipe_food_name)
                    
                    # Add the image URL reference to the structured output
                    step["image_url"] = image_url # None -> if no url
                else:
                    step["image_url"] = None
            
            print("✅ Completed image processing for all steps.")
        
        return recipe_json

    except Exception as e:
        print(f"❌ Error generating recipe: {e}")
        return None
