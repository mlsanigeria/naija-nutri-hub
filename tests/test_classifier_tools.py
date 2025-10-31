from src.food_classifier.classifier_tools import classify_food_image_azure


def test_food_image():
    image_path = ""  # Replace with your actual image path
    result = classify_food_image_azure(image_path)
    print("Predicted food:", result)
        
if __name__ == "__main__":
    test_food_image()
