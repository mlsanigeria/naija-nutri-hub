
# Food Classification and Enrichment Tool


import io
import os
import re
import stat
import json
import shutil
import yaml
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Azure imports
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
from openai import AzureOpenAI

# YOLO import (for fallback classification)
try:
    from ultralytics import YOLO
except:
    pass

load_dotenv()


# Utility Helpers

def get_latest_path(root_dir):
    files = {filename.split('train')[-1]: filename for filename in os.listdir(root_dir) if filename.startswith("train")}
    return files[max(files.keys())]


def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def get_weights():
    """
    Downloads and prepares YOLO weights if not present.
    """
    if not os.path.exists("./weights/best.pt"):
        weights_dir = "./weights"
        dst = os.path.join(weights_dir, "best.pt")
        os.makedirs(weights_dir, exist_ok=True)

        try:
            os.system('git clone https://huggingface.co/GboyeStack/NigerFoodAi ./model_clone')
        except:
            raise Exception(" Unable to download model weights. Check your internet connection.")
        else:
            shutil.copytree('./model_clone/runs', './runs')
            shutil.rmtree('./model_clone', onerror=remove_readonly)
            weights_path = f"./runs/classify/{get_latest_path('./runs/classify')}/weights/last.pt"
            shutil.copy(weights_path, dst)
            shutil.rmtree('./runs', onerror=remove_readonly)

    return "./weights/best.pt"


def load_model(model_path: str):
    """
    Loads the YOLO classification model from weights.
    """
    model = YOLO(model_path)
    return model



# Azure Custom Vision Classification

def classify_food_image_azure(img_bytes: bytes) -> str:
    """
    Classifies a food image using Azure Custom Vision.
    Returns the top predicted food name.
    """
    try:
        Image.open(io.BytesIO(img_bytes))  
    except Exception as e:
        raise ValueError(f"Error opening image: {e}")

    prediction_key = os.environ.get("VISION_PREDICTION_KEY")
    endpoint = os.environ.get("VISION_PREDICTION_ENDPOINT")
    project_id = os.environ.get("VISION_PROJECT_ID")
    publish_iteration_name = os.environ.get("VISION_ITERATION_NAME")

    if not all([prediction_key, endpoint, project_id, publish_iteration_name]):
        raise EnvironmentError("Missing Azure Custom Vision environment variables.")

    credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
    predictor = CustomVisionPredictionClient(endpoint, credentials)

    try:
        results = predictor.classify_image(project_id, publish_iteration_name, img_bytes)
        if results.predictions:
            top_prediction = max(results.predictions, key=lambda p: p.probability)
            return top_prediction.tag_name, float(top_prediction.probability)
        else:
            return "No prediction returned", 0.0
    except Exception as e:
        print(f"Azure classification failed: {e}")
        return "prediction failed", 0.0
    #return {"food_name": "Jollof Rice", "confidence": 0.97}



# YOLO Fallback Classifier

def classify_food_image(image):
    """Fallback local classification using YOLO."""
    model = load_model("./weights/best.pt")
    result = model(image)[0]
    predicted_food = model.names[result.probs.top1]
    return predicted_food


# TF-IDF Matching (Backup)

def get_closest_food_tfidf(food_name, dataset_path="./data/Nigerian Foods.csv", threshold=0.5):
    try:
        df = pd.read_csv(dataset_path)
        if "Food_Name" not in df.columns:
            raise ValueError("Dataset must contain a 'Food_Name' column.")

        names = df["Food_Name"].fillna("").tolist()
        vectorizer = TfidfVectorizer().fit(names + [food_name])
        vectors = vectorizer.transform(names + [food_name])
        similarities = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

        best_match_idx = similarities.argmax()
        best_score = similarities[best_match_idx]
        return df.iloc[best_match_idx]["Food_Name"] if best_score >= threshold else None
    except Exception as e:
        print(f" TF-IDF matching failed: {e}")
        return None



# Azure OpenAI Enrichment

def enrich_food_info(food_name):
    def load_prompts(path="./src/food_classifier/classifier_prompt.yml"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            return {
                "enrichment_prompt": "Provide key facts about {{food_name}} including ingredients, origin, and description in JSON format."
            }

    prompts = load_prompts()
    enrichment_prompt = prompts["enrichment_prompt"].replace("{{food_name}}", food_name)

    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_BASE_URL", ""),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", ""),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01-preview"),
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are a helpful Nigerian food expert."},
                {"role": "user", "content": enrichment_prompt},
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
            "main_ingredients": info.get("main_ingredients", []),
        }

    except Exception as e:
        print(f" GenAI enrichment failed: {e}")
        return {
            "food_name": food_name,
            "description": "No description available.",
            "origin": "Nigeria",
            "spice_level": "Unknown",
            "main_ingredients": [],
        }




# Main Pipeline Function

def classify_and_enrich(image_path):
    """
    Takes a food image, classifies it (mock Azure), then enriches the result.
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    try:
        azure_result = classify_food_image_azure(img_bytes)
        food_name = azure_result.get("food_name")
        confidence = azure_result.get("confidence", 0.9)
        source = "azure"

        print(f"Azure mock classification successful: {food_name}")

    except Exception as e:
        print(f" Azure classification failed, falling back to YOLO: {e}")
        image = Image.open(image_path).convert("RGB")
        food_name = classify_food_image(image)
        confidence = 0.7
        source = "yolo"

    if confidence < 0.75:
        similar = get_closest_food_tfidf(food_name)
        if similar:
            print(f" Low confidence, using TF-IDF match: {similar}")
            food_name = similar
            source = "tfidf"

    enriched = enrich_food_info(food_name)
    enriched["confidence"] = confidence
    enriched["source"] = source

    print("\n Final Enriched Output:")
    print(json.dumps(enriched, indent=4))
    return enriched



# Test Run

if __name__ == "__main__":
    test_image = os.path.join(os.path.dirname(__file__), "test_images", "image.jpeg")

    if not os.path.exists(test_image):
        print(" No test image found. Please add one under src/food_classifier/test_images/")
    else:
        classify_and_enrich(test_image)