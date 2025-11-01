import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher

load_dotenv()
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")


# 0. TF-IDF dataset search
def search_dataset_tfidf(food_name: str, dataset_path: str = "data/Nigerian Foods.csv") -> Dict[str, Any]:
    try:
        if not os.path.exists(dataset_path):
            return {"source": "dataset", "data_found": False, "error": "Dataset not found"}

        df = pd.read_csv(dataset_path)

        
        name_col = None
        for c in ["Food_Name", "food_name", "name"]:
            if c in df.columns:
                name_col = c
                break
        if not name_col:
            return {"source": "dataset", "data_found": False, "error": "No name column found"}

        # TF-IDF similarity
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(df[name_col].astype(str))
        q = vectorizer.transform([food_name])
        sims = cosine_similarity(q, tfidf_matrix).flatten()
        best_idx = sims.argmax()
        best_score = float(sims[best_idx])

        if best_score < 0.2:
            return {"source": "dataset", "data_found": False, "error": "No close match found", "best_score": best_score}

        row = df.iloc[best_idx].to_dict()
        row["similarity_score"] = best_score
        row["data_found"] = True
        row["source"] = "dataset"
        return row

    except Exception as e:
        return {"source": "dataset", "data_found": False, "error": str(e)}


# 1. Get nutrition info directly from dataset (structured form)
def get_nutrition_from_dataset(food_name: str, dataset_path: str = "data/Nigerian Foods.csv") -> Dict[str, Any]:
    """
    Retrieves structured data (region, class, price, etc.) from the dataset using TF-IDF search.
    The dataset should contain:
    Food_Name, Main_Ingredients, Description, Food_Health, Food_Class, Region, Spice_Level, Price_Range
    """
    try:
        result = search_dataset_tfidf(food_name, dataset_path)
        if not result.get("data_found"):
            return {"source": "dataset", "data_found": False, "error": result.get("error")}

        nutrition_info = {
            "food_name": result.get("Food_Name") or result.get("food_name"),
            "region": result.get("Region"),
            "main_ingredients": result.get("Main_Ingredients"),
            "food_class": result.get("Food_Class"),
            "food_health": result.get("Food_Health"),
            "spice_level": result.get("Spice_Level"),
            "price_range": result.get("Price_Range"),
            "description": result.get("Description"),
        }

        return {
            "source": "dataset",
            "data_found": True,
            "match_score": result.get("similarity_score"),
            "nutrition_facts": nutrition_info,
        }

    except Exception as e:
        return {"source": "dataset", "data_found": False, "error": str(e)}


# 2. TheMealDB fetch
def get_nutrition_from_mealdb(food_name: str) -> Dict[str, Any]:
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={food_name}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data.get("meals"):
            return {"source": "TheMealDB", "data_found": False}

        meal = data["meals"][0]
        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}")
            meas = meal.get(f"strMeasure{i}")
            if ing and ing.strip():
                ingredients.append({"ingredient": ing.strip(), "measure": (meas or "").strip()})

        return {
            "source": "TheMealDB",
            "data_found": True,
            "food_name": meal.get("strMeal"),
            "category": meal.get("strCategory"),
            "area": meal.get("strArea"),
            "origin": meal.get("strArea"),
            "ingredients": ingredients,
            "instructions": (meal.get("strInstructions") or "")[:500],
        }

    except Exception as e:
        return {"source": "TheMealDB", "data_found": False, "error": str(e)}


# 3. Spoonacular fetch
def get_nutrition_from_spoonacular(food_name: str) -> Dict[str, Any]:
    api_key = SPOONACULAR_API_KEY
    if not api_key:
        return {"source": "Spoonacular", "data_found": False, "error": "Missing API key"}

    try:
        base_url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {"query": food_name, "addRecipeNutrition": True, "number": 5, "apiKey": api_key}
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            return {"source": "Spoonacular", "data_found": False, "error": "No results"}

        def sim(a, b): return SequenceMatcher(None, a.lower(), b.lower()).ratio()
        best = max(results, key=lambda r: sim(food_name, r.get("title", "")))
        match_score = sim(food_name, best.get("title", ""))

        nutrients = best.get("nutrition", {}).get("nutrients", []) or []
        if not nutrients and best.get("id"):
            widget_url = f"https://api.spoonacular.com/recipes/{best['id']}/nutritionWidget.json"
            wresp = requests.get(widget_url, params={"apiKey": api_key}, timeout=10)
            if wresp.status_code == 200:
                wdata = wresp.json()
                nutrients = wdata.get("good", []) + wdata.get("bad", [])
                if not nutrients:
                    if "calories" in wdata:
                        nutrients = [{"name": "Calories", "amount": wdata.get("calories")}]
                    for k in ("carbs", "fat", "protein"):
                        if k in wdata:
                            nutrients.append({"name": k, "amount": wdata.get(k)})

        if not nutrients:
            return {"source": "Spoonacular", "data_found": False, "error": "No nutrient data", "match_score": match_score}

        normalized = {}
        for n in nutrients:
            name = (n.get("name") or n.get("title") or "").lower()
            amt = n.get("amount")
            try:
                normalized[name] = float(amt)
            except Exception:
                s = str(amt)
                num = "".join(ch for ch in s if (ch.isdigit() or ch == '.' or ch == '-'))
                normalized[name] = float(num) if num else None

        def lookup(keys):
            for k in keys:
                for n in normalized:
                    if k in n:
                        return normalized[n]
            return None

        nutrition_info = {
            "calories": lookup(["calories", "energy"]),
            "protein_g": lookup(["protein"]),
            "fat_g": lookup(["fat"]),
            "carbohydrates_g": lookup(["carbohydrate", "carbs", "carbohydrates"]),
            "fiber_g": lookup(["fiber", "dietary fiber"]),
            "sugar_g": lookup(["sugar", "sugars"]),
            "cholesterol_mg": lookup(["cholesterol"]),
            "sodium_mg": lookup(["sodium", "salt"]),
        }

        return {
            "source": "Spoonacular",
            "data_found": True,
            "food_name": best.get("title", food_name),
            "match_score": match_score,
            "nutrition_facts": nutrition_info,
            "raw_result": best,
        }

    except Exception as e:
        return {"source": "Spoonacular", "data_found": False, "error": str(e)}


# 4. Combine all sources
def combine_nutrition_sources(
    dataset_data: Optional[dict],
    mealdb_data: dict,
    spoon_data: dict,
    serving_description: Optional[str] = None,
    extra_inputs: Optional[str] = None,
) -> Dict[str, Any]:
    has_dataset = bool(dataset_data and dataset_data.get("data_found"))
    has_mealdb = bool(mealdb_data and mealdb_data.get("data_found"))
    has_spoon = bool(spoon_data and spoon_data.get("data_found"))

    retrieved_dataset_context = json.dumps(dataset_data or {}, default=str, indent=2)
    api_context = json.dumps(
        {k: v for k, v in {"mealdb": mealdb_data, "spoonacular": spoon_data}.items() if v and v.get("data_found")},
        default=str, indent=2
    )

    inferred_context = {
        "available_sources": {"dataset": has_dataset, "mealdb": has_mealdb, "spoonacular": has_spoon},
        "notes": "No rule-based inferences applied; LLM aggregates evidence.",
    }

    food_name = (
        (dataset_data or {}).get("Food_Name")
        or (dataset_data or {}).get("food_name")
        or (spoon_data or {}).get("food_name")
        or (mealdb_data or {}).get("food_name")
    )

    return {
        "food_name": food_name,
        "portion_size": serving_description or "1 serving",
        "retrieved_dataset_context": retrieved_dataset_context,
        "api_context": api_context,
        "inferred_context": json.dumps(inferred_context, indent=2),
        "sources": {"dataset": has_dataset, "mealdb": has_mealdb, "spoonacular": has_spoon},
        "extra_inputs": str(extra_inputs) if extra_inputs is not None else None,
    }


# 5. Formatter
def format_nutrition_output(data: dict) -> Dict[str, Any]:
    return {
        "food_name": data.get("food_name"),
        "portion_size": data.get("portion_size"),
        "sources": data.get("sources", {}),
        "retrieved_dataset_context": data.get("retrieved_dataset_context"),
        "api_context": data.get("api_context"),
        "inferred_context": data.get("inferred_context"),
        "extra_inputs": data.get("extra_inputs"),
    }


# 6. Quick test block
if __name__ == "__main__":
    q = "Yam and egg"
    ds = get_nutrition_from_dataset(q)
    md = get_nutrition_from_mealdb(q)
    sp = get_nutrition_from_spoonacular(q)
    combined = combine_nutrition_sources(ds, md, sp, serving_description="1 serving")
    print(json.dumps(format_nutrition_output(combined), indent=2))





