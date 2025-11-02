from classifier_tools import classify_food_image, enrich_food_info
from PIL import Image
import os
import json

def classify_image(image) -> dict:
    """
    Classifies a food image and enriches the result with contextual info.
    """
    predicted_food = classify_food_image(image)
    enriched_info = enrich_food_info(predicted_food)
    return enriched_info

if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "test_images", "image.jpeg")
    image = Image.open(image_path).convert("RGB")
    result = classify_image(image)
    print(json.dumps(result, indent=4))


