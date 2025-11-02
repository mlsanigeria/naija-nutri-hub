try:
    from ultralytics import YOLO
except:
    import os
    os.system('pip uninstall ultralytics -y')
    os.system('pip install ultralytics')
    from ultralytics import YOLO

from PIL import Image
import os
import stat
import shutil
import pandas as pd
import json
from openai import AzureOpenAI
from dotenv import load_dotenv
load_dotenv()
import yaml
import json
import re

def load_prompts(path="./src/food_classifier/classifier_prompt.yml"):
    """Load all classifier prompts from YAML."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise Exception(f"Failed to load prompts: {e}")






def get_latest_path(root_dir):
    files = {filename.split('train')[-1]: filename for filename in os.listdir(root_dir) if filename.startswith("train")}
    return files[max(files.keys())]

def remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def get_weights():
    if not os.path.exists("./weights/best.pt"):
        weights_dir = "./weights"
        dst = os.path.join(weights_dir, "best.pt")
        os.makedirs(weights_dir, exist_ok=True)
        try:
            os.system('git clone https://huggingface.co/GboyeStack/NigerFoodAi ./model_clone')
        except:
            raise Exception("Unable to download model weights. Please check your internet connection.")
        else:
            shutil.copytree('./model_clone/runs','./runs')
            shutil.rmtree('./model_clone',onerror=remove_readonly)
            weights_path=f"./runs/classify/{get_latest_path('./runs/classify')}/weights/last.pt"
            shutil.copy(weights_path,dst)
            shutil.rmtree('./runs',onerror=remove_readonly)

    return "./weights/best.pt"

def load_model(model_path: str):
    model = YOLO(model_path)
    return model



def classify_food_image(image) -> str:
    model_path = os.path.join(os.path.dirname(__file__), "weights", "best.pt")
    model_path = os.path.abspath(model_path)
    classifier = load_model(model_path)
    predicted_food = classifier.names[classifier(image)[0].probs.top1]
    return predicted_food.capitalize()  



def load_food_dataset(path: str = "./data/Nigerian Foods.csv"):
    """Loads Nigerian food dataset."""
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise Exception(f"Unable to load dataset: {e}")

def get_food_base_info(food_name: str):
    """Returns base info for a food item from the dataset."""
    df = load_food_dataset()
    match = df[df['Food_Name'].str.lower() == food_name.lower()]
    
    if not match.empty:
        row = match.iloc[0]
        return {
            "name": row['Food_Name'],
            "description": row.get('Description', None),
            "origin": row.get('Origin', None),
            "spice_level": row.get('Spice_Level', None),
            "main_ingredients": row.get('Main_Ingredients', None)
        }
    else:
        return {"name": food_name}





def enrich_food_info(predicted_food: str):
    """
    Enriches a classified food name with cultural and nutritional context using Azure OpenAI.
    """

    food_name = predicted_food.strip().capitalize()
    prompts = load_prompts()
    enrichment_prompt = prompts.get("enrichment_prompt", "").replace("{{food_name}}", food_name)

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

        raw_text = response.choices[0].message.content.strip()
        cleaned_text = re.sub(r"```json|```", "", raw_text).strip()
        info = json.loads(cleaned_text)

        return {
            "food_name": info.get("food_name", food_name),
            "description": info.get("description", "No description available."),
            "origin": info.get("origin", "Nigeria"),
            "spice_level": info.get("spice_level", "Medium"),
            "main_ingredients": info.get("main_ingredients", [])
        }

    except Exception as e:
        print(f"❌ Azure enrichment failed: {e}")
        return {
            "food_name": food_name,
            "description": "Unknown",
            "origin": "Unknown",
            "spice_level": "Unknown",
            "main_ingredients": []
        }


    return enriched_info

