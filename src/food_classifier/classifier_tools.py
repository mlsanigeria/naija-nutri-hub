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
from rapidfuzz import fuzz
import base64
import yaml
import openai

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
        # Image.open(io.BytesIO(img_bytes))  
        pass
    except Exception as e:
        raise ValueError(f"Error opening image: {e}")

    # Loading Credentials from Environment Variables
    prediction_key = os.getenv("VISION_PREDICTION_KEY")
    endpoint = os.getenv("VISION_PREDICTION_ENDPOINT")
    project_id = os.getenv("VISION_PROJECT_ID")
    publish_iteration_name = os.getenv("VISION_ITERATION_NAME")

    if not all([prediction_key, endpoint, project_id, publish_iteration_name]):
        raise EnvironmentError("Missing Azure Custom Vision environment variables.")

    credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})
    predictor = CustomVisionPredictionClient(endpoint, credentials)

    try:
        results = predictor.classify_image(project_id, publish_iteration_name, img_bytes)
        if results.predictions:
            top_prediction = max(results.predictions, key=lambda p: p.probability)
            result = {
                "food_name": top_prediction.tag_name,
                "confidence": float(top_prediction.probability)
            }
            return result
        else:
            return {"food_name": "Unknown", "confidence": 0.0}
    except Exception as e:
        print(f"Azure classification failed: {e}")
        return {"food_name": "Error", "confidence": 0.0}
    #return {"food_name": "Jollof Rice", "confidence": 0.97}
    #return {"food_name": "garriandgrounut", "confidence": 0.60}
    #return {"food_name": "Efo riro", "confidence": 0.97}


# YOLO Fallback Classifier

def classify_food_image(image):
    """Fallback local classification using YOLO."""
    model = load_model("./weights/best.pt")
    result = model(image)[0]
    predicted_food = model.names[result.probs.top1]
    return predicted_food


# TF-IDF Matching 
def get_closest_food_tfidf(query, dataset_path="data/Nigerian Foods.csv", min_fuzzy_score=50):
    df = pd.read_csv(dataset_path)
    food_names = df["Food_Name"].astype(str).tolist()

    # --- TF-IDF similarity ---
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(food_names)
    query_vec = vectorizer.transform([query])
    cosine_sim = cosine_similarity(query_vec, tfidf_matrix).flatten()

    best_idx = cosine_sim.argmax()
    best_food = food_names[best_idx]
    best_score = cosine_sim[best_idx]

    # --- Fuzzy token-based matching ---
    fuzzy_scores = {name: fuzz.token_set_ratio(query.lower(), name.lower()) for name in food_names}
    best_fuzzy_food = max(fuzzy_scores, key=fuzzy_scores.get)
    best_fuzzy_score = fuzzy_scores[best_fuzzy_food]

    # --- Select best match ---
    if best_fuzzy_score >= min_fuzzy_score or best_score > 0.2:
        matched = best_fuzzy_food if best_fuzzy_score >= min_fuzzy_score else best_food
        print(f"🔍 Matched '{query}' → '{matched}' (Fuzzy={best_fuzzy_score:.2f}, TF-IDF={best_score:.2f})")
    else:
        print(f"⚠️ No strong match for '{query}' (TF-IDF={best_score:.2f}, Fuzzy={best_fuzzy_score:.2f})")
        return None

    # --- Return only the selected columns ---
    row = df[df["Food_Name"].str.lower() == matched.lower()].iloc[0]
    return {
        "food_name": row["Food_Name"],
        "description": row["Description"],
        "spice_level": row["Spice_Level"],
        "main_ingredients": row["Main_Ingredients"],
    }



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
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
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



def load_prompt_from_yaml(file_path="prompts/classifier_prompt.yml"):
    """
    Loads the GenAI classification prompt from a YAML file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_data = yaml.safe_load(f)
        return prompt_data.get("prompt", "")
    except Exception as e:
        print(f" Could not load classifier_prompt.yml: {e}")
        return (
            "You are an expert Nigerian food recognition assistant. "
            "Identify the food in this image and provide key information."
        )


def classify_food_genai(image_path: str):
    """
    Uses GPT-Vision (OpenAI) for food classification when both Azure and YOLO fail or are uncertain.
    Loads classification logic from classifier_prompt.yml and returns:
    food_name, description, spice_level, main_ingredients, confidence, source.
    """

    # Load image
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # Load dynamic prompt from YAML
    prompt_text = load_prompt_from_yaml()

    print("🤖 Using GenAI fallback classification with enriched output...")

    # Append structured output instruction
    full_prompt = f"""
{prompt_text}

Please respond **strictly** in valid JSON with the following fields:
{{
    "food_name": "string",
    "description": "string",
    "spice_level": "string",
    "main_ingredients": ["list", "of", "ingredients"],
    "confidence": 0.0
}}
"""

    try:
        # OpenAI multimodal call
        response = openai.ChatCompletion.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are an expert Nigerian food classifier."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
                    ],
                },
            ],
            temperature=0.2,
        )

        reply = response["choices"][0]["message"]["content"].strip()

        
        try:
            parsed = json.loads(reply)
        except json.JSONDecodeError:
            print(" Model response not valid JSON, using fallback parser.")
            parsed = {
                "food_name": reply,
                "description": "A traditional Nigerian dish.",
                "spice_level": "Medium",
                "main_ingredients": ["Unknown"],
                "confidence": 0.6
            }

        parsed["source"] = "genai"

        print(f" GenAI classification successful: {parsed['food_name']} ({parsed['confidence']:.2f})")

        return parsed

    except Exception as e:
        print(f" GenAI classification failed: {e}")
        return {
            "food_name": "Unknown",
            "description": "Unable to classify image.",
            "spice_level": "Unknown",
            "main_ingredients": [],
            "confidence": 0.0,
            "source": "genai_error"
        }

# Main Pipeline Function


def classify_and_enrich(image_path):
    """
    Multi-stage food classification workflow:
    1. Try Azure classification first
    2. If Azure confidence < 0.75 → fallback to YOLO
    3. If YOLO confidence < 0.7 → fallback to GenAI
    4. Always validate and enrich with TF-IDF if food exists in dataset
    """

    # Step 1: Read image bytes
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    food_name, confidence, source = None, 0, None

    # Step 2: Azure classification
    try:
        azure_result = classify_food_image_azure(img_bytes)
        food_name = azure_result.get("food_name")
        confidence = azure_result.get("confidence", 0.9)
        source = "azure"
        print(f" Azure classification: {food_name} ({confidence:.2f})")
    except Exception as e:
        print(f" Azure classification failed: {e}")
        food_name, confidence, source = None, 0, "azure_failed"

    # Step 3: YOLO fallback if Azure confidence is low
    if not food_name or confidence < 0.75:
        print("⚙️ Switching to YOLO classification...")
        image = Image.open(image_path).convert("RGB")
        food_name = classify_food_image(image)
        confidence = 0.7  # assume default confidence for YOLO
        source = "yolo"
        print(f" YOLO classification: {food_name} ({confidence:.2f})")

    # Step 4: GenAI fallback if YOLO confidence is still low
    if confidence < 0.7:
        print("⚙️ Switching to GenAI image classification...")
        try:
            genai_result = classify_food_genai(image_path)
            food_name = genai_result.get("food_name")
            confidence = genai_result.get("confidence", 0.85)
            source = "genai"
            print(f" GenAI classification: {food_name} ({confidence:.2f})")
        except Exception as e:
            print(f" GenAI classification failed: {e}")

    # Step 5: Always run TF-IDF correction (if food name exists)
    tfidf_data = get_closest_food_tfidf(food_name)
    if tfidf_data:
        food_name = tfidf_data["food_name"]
        description = tfidf_data["description"]
        spice_level = tfidf_data["spice_level"]
        main_ingredients = tfidf_data["main_ingredients"]
        source = "tfidf"
    else:
        enriched = enrich_food_info(food_name)
        description = enriched.get("description", "")
        spice_level = enriched.get("spice_level", "")
        main_ingredients = enriched.get("main_ingredients", "")

    # Step 6: Final result
    final_result = {
        "food_name": food_name,
        "description": description,
        "spice_level": spice_level,
        "main_ingredients": main_ingredients,
        "confidence": confidence,
        "source": source
    }

    print("\n Final Enriched Output:")
    print(json.dumps(final_result, indent=4))
    return final_result


# Test Run

if __name__ == "__main__":
    test_image = os.path.join(os.path.dirname(__file__), "test_images", "test_2.jpeg")

    if not os.path.exists(test_image):
        print(" No test image found. Please add one under src/food_classifier/test_images/")
    else:
        print("\n Final Enriched Output:")
        print(classify_and_enrich(test_image))
