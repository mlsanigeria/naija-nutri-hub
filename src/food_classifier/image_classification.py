from classifier_tools import classify_food_image

from PIL import Image

def classify_image(image) -> str:
    """
    Classifies a food image and returns the predicted food name.
    Args:
        image: The image to be classified.
    """
    
    predicted_food = classify_food_image(image)

    return predicted_food

if __name__ == "__main__":
    #This ensures that the script runs only when executed directly via command prompt
    image_path = "./test_images/image.jpg"  
    image=Image.open(image_path).convert("RGB")
    predicted_food = classify_image(image)
    print(f"Predicted food: {predicted_food}")


