import os
import yaml
import pandas as pd
import numpy as np
from openai import AzureOpenAI
from recipe_tools import get_recipe_from_mealdb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv


load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_BASE_URL"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
)

AZURE_MODEL_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# dataset
DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/Nigerian Foods.csv")

df = pd.read_csv(DATA_PATH)
df.columns = [col.strip().lower() for col in df.columns]


def semantic_search_in_dataset(food_name: str, dataset_path: str, top_k: int = 3):
    """
    instead of a heavy SentenceTransformer model.
    """
    if not os.path.exists(dataset_path):
        print("Dataset not found.")
        return None

    df = pd.read_csv(dataset_path)
    df.columns = [col.strip().lower() for col in df.columns]

    if "food_name" not in df.columns:
        print("'food_name' column not found in dataset.")
        return None

    food_texts = df["food_name"].astype(str).tolist()  

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer().fit(food_texts + [food_name])
    corpus_embeddings = vectorizer.transform(food_texts)
    query_embedding = vectorizer.transform([food_name])

    # Compute cosine similarity
    scores = cosine_similarity(query_embedding, corpus_embeddings)[0]
    top_results = np.argsort(-scores)[:top_k]

    best_idx = int(top_results[0])
    best_score = float(scores[best_idx])

    if best_score < 0.5:
        print(f"No strong semantic match found (best score={best_score:.2f}).")
        return None

    best_match = df.iloc[best_idx].to_dict()
    best_match["similarity_score"] = round(best_score, 2)
    print(f"semantic match found: {best_match['food_name']} (score={best_score:.2f})")

    return best_match


def generate_structured_recipe(food_name: str):
    """
    Generates a structured recipe for a given food item.
    Priority:
      1. Semantic search (local dataset)
      2. TheMealDB API
      3. Model generation (Azure OpenAI)
    """

    print(f"Starting recipe generation for: {food_name}\n")

    # STEP 1: Semantic Search in Local Dataset
    print("🔍 Step 1: Performing semantic search in dataset...")
    dataset_recipe = semantic_search_in_dataset(food_name, DATA_PATH)

    if dataset_recipe:
        context = {
            "food_name": dataset_recipe.get("food_name", food_name),
            "description": dataset_recipe.get("description", "A delicious Nigerian dish."),
            "main_ingredients": dataset_recipe.get("main_ingredients", ""),
            "region": dataset_recipe.get("region", "Nationwide"),
            "spice_level": dataset_recipe.get("spice_level", "Medium"),
        }
    else:
        print("No semantic match found. Proceeding with fallback context.\n")
        context = {
            "food_name": food_name,
            "description": "",
            "main_ingredients": "",
            "region": "",
            "spice_level": "",
        }

    # STEP 2: TheMealDB API
    print("🍲 Step 2: Fetching from TheMealDB API...")
    api_recipe = get_recipe_from_mealdb(food_name)
    if api_recipe:
        print("✅ Recipe fetched from TheMealDB API!\n")
        return {
            "source": "themealdb_api",
            "data": api_recipe
        }

    # STEP 3: Generate with Model (Azure OpenAI)
    print("🤖 Step 3: Generating recipe using Azure OpenAI...\n")
    prompt_file = os.path.join(os.path.dirname(__file__), "recipe_prompt.yml")

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)

    template = prompts["prompt"]

    filled_prompt = (
        template.replace("{{ food_name }}", context["food_name"])
                .replace("{{ description }}", context["description"])
                .replace("{{ main_ingredients }}", context["main_ingredients"])
                .replace("{{ region }}", context["region"])
                .replace("{{ spice_level }}", context["spice_level"])
    )

    try:
        completion = client.chat.completions.create(
            model=AZURE_MODEL_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian chef assistant."},
                {"role": "user", "content": filled_prompt}
            ],
            response_format={"type": "json_object"}
        )

        import json

        try:
            structured_recipe = json.loads(completion.choices[0].message.content)
        except json.JSONDecodeError:
    # fallback if model returns invalid JSON-like text
            structured_recipe = {
                "raw_response": completion.choices[0].message.content,
                "note": "Model returned a non-JSON string. Please validate output."
            }

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

