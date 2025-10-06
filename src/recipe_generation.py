import os
import pandas as pd
import requests
from openai import AzureOpenAI


DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/Nigerian Foods.csv")

# === Azure OpenAI client ===

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="",
    api_key="",
)

# === Load dataset ===
def load_food_dataset():
    try:
        df = pd.read_csv(DATA_PATH)
        return df
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return pd.DataFrame()

# === Search dataset ===
def search_local_recipe(food_name: str):
    df = load_food_dataset()
    results = df[df["Food_Name"].str.contains(food_name, case=False, na=False)]
    if not results.empty:
        return results.iloc[0].to_dict()
    return None

# === Query TheMealDB API ===
def fetch_recipe_from_mealdb(food_name: str):
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data and data.get("meals"):
            return data["meals"][0]
    return None

# === Generate recipe via GPT ===
def generate_recipe_description(food_name, local_data=None, api_data=None):
    context_parts = []
    if local_data:
        context_parts.append(f"Local Nigerian dataset: {local_data}")
    if api_data:
        context_parts.append(f"TheMealDB data: {api_data['strInstructions']}")
    
    context = "\n\n".join(context_parts) if context_parts else "No data found, generate from scratch."

    prompt = f"""
You are a Nigerian culinary assistant. Generate a detailed recipe for '{food_name}'.
Use the following context if available:

{context}

Include:
1. Short description
2. Main ingredients (with quantities)
3. Step-by-step instructions
4. Estimated calories (if known)
5. Suggested region and spice level
    """

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a Nigerian culinary AI that provides grounded recipes."},
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()

# === Main recipe generation function ===
def get_recipe(food_name: str):
    local_data = search_local_recipe(food_name)
    api_data = fetch_recipe_from_mealdb(food_name)
    recipe = generate_recipe_description(food_name, local_data, api_data)
    return recipe

# === Test run ===
if __name__ == "__main__":
    food = input("Enter a Nigerian dish: ")
    recipe = get_recipe(food)
    print("\n===== Recipe =====\n")
    print(recipe)
