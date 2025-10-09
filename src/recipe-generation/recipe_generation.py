import os
import yaml
import pandas as pd
import numpy as np
from openai import AzureOpenAI
from recipe_tools import get_recipe_from_mealdb
from sentence_transformers import SentenceTransformer, util

# Initialize OpenAI client
client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="your-endpoint-url",
    api_key="your-api-key",
)

# Initialize embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Path to dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "Nigerian Foods.csv")


def semantic_search_in_dataset(food_name: str, dataset_path: str, top_k: int = 3):
    """
    Performs semantic search on the local dataset to find the closest matches.
    """
    if not os.path.exists(dataset_path):
        print( "Dataset not found.")
        return None

    df = pd.read_csv(dataset_path)

    #
    if "food_name" not in df.columns:
        print("'food_name' column not found in dataset.")
        return None

    # Embed all dataset food names
    food_texts = df["food_name"].astype(str).tolist()
    corpus_embeddings = embedder.encode(food_texts, convert_to_tensor=True)

    # Embed user query
    query_embedding = embedder.encode(food_name, convert_to_tensor=True)

    # Compute similarity
    scores = util.pytorch_cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = np.argsort(-scores)[:top_k]

    best_idx = int(top_results[0])
    best_score = float(scores[best_idx])

    if best_score < 0.5:
        print(f"No strong semantic match found (best score={best_score:.2f}).")
        return None

    best_match = df.iloc[best_idx].to_dict()
    best_match["similarity_score"] = round(best_score, 2)
    print(f" Semantic match found: {best_match['food_name']} (score={best_score:.2f})")

    return best_match


def generate_structured_recipe(food_name: str):
    """
    Generates a structured recipe for a given food item.
    Priority:
      1. Semantic search (local dataset)
      2. TheMealDB API
      3. Model generation (YAML prompt)
    """

    print(f"Starting recipe generation for: {food_name}\n")

    # STEP 1: Semantic Search in Local Dataset
    print(" Step 1: Performing semantic search in dataset...")
    dataset_recipe = semantic_search_in_dataset(food_name, DATA_PATH)

    if dataset_recipe:
        print("Recipe context found from dataset!\n")
        context = {
            "food_name": dataset_recipe.get("food_name", food_name),
            "description": dataset_recipe.get("description", "A delicious Nigerian dish."),
            "main_ingredients": dataset_recipe.get("main_ingredients", ""),
            "region": dataset_recipe.get("region", "Nationwide"),
            "spice_level": dataset_recipe.get("spice_level", "Medium"),
        }
    else:
        print(" No semantic match found. Proceeding with fallback context.\n")
        context = {
            "food_name": food_name,
            "description": "",
            "main_ingredients": "",
            "region": "",
            "spice_level": "",
        }

    # STEP 2: Try TheMealDB API
    print("Step 2: Fetching from TheMealDB API...")
    api_recipe = get_recipe_from_mealdb(food_name)
    if api_recipe:
        print(" Recipe fetched from TheMealDB API!\n")
        return {
            "source": "themealdb_api",
            "data": api_recipe
        }

    # STEP 3: Generate with Model (YAML-based prompt)
    print(" Step 3: Generating recipe using model (Azure OpenAI)...\n")
    prompt_file = os.path.join(os.path.dirname(__file__), "recipe_prompt.yml")
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    template = prompts["prompt"]

    # Fill placeholders with dataset context
    filled_prompt = (
        template.replace("{{ food_name }}", context["food_name"])
                .replace("{{ description }}", context["description"])
                .replace("{{ main_ingredients }}", context["main_ingredients"])
                .replace("{{ region }}", context["region"])
                .replace("{{ spice_level }}", context["spice_level"])
    )

    print(" Prompt being sent to model:\n")
    print(filled_prompt, "\n") 

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian chef assistant."},
                {"role": "user", "content": filled_prompt}
            ],
            response_format={"type": "json_object"}
        )

        structured_recipe = completion.choices[0].message.content
        print("Model responded with structured recipe!\n")  
        return {
            "source": "model",
            "data": structured_recipe
        }

    except Exception as e:
        print("Error during model generation!\n")
        print("Error message:", str(e))
        return {
            "source": "error",
            "error": str(e),
            "context_used": context
        }


# Quick test
if __name__ == "__main__":
    result = generate_structured_recipe("Efo riro")
    print(result)
