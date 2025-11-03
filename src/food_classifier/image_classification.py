from classifier_tools import classify_food_image, classify_food_image_azure
import io

from PIL import Image

def classify_image(image) -> str:
    """
    Classifies a food image and returns the predicted food name.
    Args:
        image: The image to be classified.
    """
    
    # predicted_food = classify_food_image(image)
    predicted_food_azure = classify_food_image_azure(image)

    return predicted_food_azure

if __name__ == "__main__":
    #This ensures that the script runs only when executed directly via command prompt
    image_path = "src/food_classifier/test_images/image.jpg"  
    image = Image.open(image_path) #.convert("RGB")
    # Pass image as bytes
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
    predicted_food = classify_image(img_bytes)
    print(f"Predicted food: {predicted_food}")


