from ultralytics import YOLO
from openai import AzureOpenAI
from PIL import Image
import os, re, json, pandas as pd, yaml
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()


def load_prompts(path="./src/food_classifier/classifier_prompt.yml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)



import shutil


def get_weights():
    weights_dir = "./weights"
    dst = os.path.join(weights_dir, "best.pt")

    
    if os.path.exists(dst):
        print(" Using existing model weights.")
        return dst

    print(" Downloading model weights from Hugging Face...")

    
    if os.path.exists("./model_clone"):
        shutil.rmtree("./model_clone", ignore_errors=True)

    os.makedirs(weights_dir, exist_ok=True)

    #
    exit_code = os.system("git clone https://huggingface.co/GboyeStack/NigerFoodAi ./model_clone")
    if exit_code != 0:
        raise Exception(" Git clone failed. Check your internet connection or Hugging Face access.")

    
    classify_dir = os.path.join("model_clone", "runs", "classify")
    if not os.path.exists(classify_dir):
        raise FileNotFoundError(" No 'runs/classify' folder found in the cloned repo. Check the repo structure.")

    subdirs = [d for d in os.listdir(classify_dir) if os.path.isdir(os.path.join(classify_dir, d))]
    if not subdirs:
        raise FileNotFoundError(" No subdirectories found inside 'runs/classify'.")

    latest_subdir = max(subdirs, key=lambda d: os.path.getmtime(os.path.join(classify_dir, d)))
    weights_path = os.path.join(classify_dir, latest_subdir, "weights", "last.pt")

    if not os.path.exists(weights_path):
        raise FileNotFoundError(" Could not find 'last.pt' in the cloned repository.")

    shutil.copy(weights_path, dst)
    print(f" Model weights copied to {dst}")

    # Clean up
    shutil.rmtree("./model_clone", ignore_errors=True)

    return dst


def load_model(model_path: str):
    return YOLO(model_path)



def classify_food_image(image):
    model = load_model(get_weights())
    results = model(image)[0]
    probs = results.probs.data.tolist()
    top_index = results.probs.top1
    top_conf = results.probs.top1conf.item()
    predicted_food = model.names[top_index]
    return predicted_food.capitalize(), top_conf

# ---------------- TF-IDF SIMILARITY SEARCH ----------------
def get_closest_food_tfidf(food_name: str, dataset_path="./data/Nigerian Foods.csv", threshold=0.5):
    df = pd.read_csv(dataset_path)
    names = df["Food_Name"].fillna("").tolist()
    vectorizer = TfidfVectorizer().fit(names + [food_name])
    vectors = vectorizer.transform(names + [food_name])
    similarities = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
    best_match_idx = similarities.argmax()
    best_score = similarities[best_match_idx]
    if best_score >= threshold:
        return df.iloc[best_match_idx]["Food_Name"]
    return None

# ---------------- GENAI ENRICHMENT ----------------
def enrich_food_info(food_name: str):
    prompts = load_prompts()
    enrichment_prompt = prompts["enrichment_prompt"].replace("{{food_name}}", food_name)

    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_BASE_URL"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian food expert."},
                {"role": "user", "content": enrichment_prompt}
            ],
            temperature=0.5,
        )

        raw = response.choices[0].message.content.strip()
        cleaned = re.sub(r"```json|```", "", raw).strip()
        info = json.loads(cleaned)

        return {
            "food_name": info.get("food_name", food_name),
            "description": info.get("description", "No description available."),
            "origin": info.get("origin", "Nigeria"),
            "spice_level": info.get("spice_level", "Medium"),
            "main_ingredients": info.get("main_ingredients", [])
        }

    except Exception as e:
        print(f" GenAI enrichment failed: {e}")
        return {
            "food_name": food_name,
            "description": "No description available.",
            "origin": "Nigeria",
            "spice_level": "Unknown",
            "main_ingredients": []
        }

# ---------------- MAIN PIPELINE ----------------
def classify_and_enrich(image):
    food_name, confidence = classify_food_image(image)

    # Low confidence or unknown category → use TF-IDF or GenAI
    if confidence < 0.75:
        similar = get_closest_food_tfidf(food_name)
        if similar:
            print(f"⚠️ Low confidence ({confidence:.2f}), using closest match: {similar}")
            food_name = similar
        else:
            print(f"⚠️ Unknown food '{food_name}', enriching with GenAI...")

    enriched = enrich_food_info(food_name)

    
    print(f"""
Food Name: {enriched['food_name']}
Description: {enriched['description']}
Origin: {enriched['origin']}
Spice Level: {enriched['spice_level']}
Main Ingredients: {', '.join(enriched['main_ingredients'])}
    """)

    return enriched


if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "test_images", "image.jpeg")
    image = Image.open(image_path).convert("RGB")
    result = classify_and_enrich(image)
