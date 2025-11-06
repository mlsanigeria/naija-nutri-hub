from classifier_tools import classify_food_image, enrich_food_info, classify_and_enrich
from PIL import Image
import os
import json

# def classify_image(image) -> dict:
    
#     # food_name = classify_food_image(image)
#     # enriched_info = enrich_food_info(food_name)
#     # classified_and_enriched = classify_and_enrich(image_path)

#     # result = {
#     #     "food_name": food_name,
#     #     "confidence": None,  
#     #     **classified_and_enriched
#     # }

#     full_info = classify_and_enrich(image)

#     return full_info
def classify_image(image) -> dict:
    # Mocked response for testing
    return {
        "label": "egusi_soup",
        "confidence": 0.92,
        "details": {
            "top_k": [
                {"label": "egusi_soup", "confidence": 0.92},
                {"label": "okro_soup", "confidence": 0.05}
            ],
            "model_version": "mock-v1"
        }
    }

if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "test_images", "image.jpg")
    # image = Image.open(image_path).convert("RGB")
    with open(image_path, "rb") as f:
        image = f.read()
    result = classify_image(image)
    print(json.dumps(result, indent=4))


