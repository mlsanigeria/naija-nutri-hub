"""
Food Classification Module for Naija Nutri Hub

This module handles image classification of Nigerian foods using AI models.
It provides functionality to identify dishes from uploaded images.
"""

import os
import base64
import logging
from typing import List, Optional, Dict, Any
from io import BytesIO
from PIL import Image
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FoodClassifier:
    """
    Food classifier using OpenAI Vision API for Nigerian food identification.
    """
    
    def __init__(self):
        """Initialize the food classifier with OpenAI client."""
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        self.model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
        
        # Common Nigerian foods for reference
        self.nigerian_foods = [
            "Jollof Rice", "Fried Rice", "Pounded Yam", "Egusi Soup", "Pepper Soup",
            "Suya", "Moi Moi", "Akara", "Plantain", "Amala", "Efo Riro", "Ogbono Soup",
            "Bitter Leaf Soup", "Afang Soup", "Okra Soup", "Banga Soup", "Ofada Rice",
            "Tuwo Shinkafa", "Masa", "Kilishi", "Chin Chin", "Puff Puff", "Bole",
            "Roasted Corn", "Coconut Rice", "Fisherman Soup", "Catfish Pepper Soup",
            "Goat Meat Pepper Soup", "Nkwobi", "Isi Ewu", "Asun", "Gbegiri Soup"
        ]

    def preprocess_image(self, image_data: bytes) -> str:
        """
        Preprocess image for classification.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Open and validate image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Resize image if too large (max 1024x1024 for efficiency)
            max_size = 1024
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert back to bytes
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            image_bytes = buffer.getvalue()
            
            # Encode to base64
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise ValueError(f"Invalid image format: {str(e)}")

    def classify_food(self, image_data: bytes) -> Dict[str, Any]:
        """
        Classify food in the provided image.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing classification results
        """
        try:
            # Preprocess image
            base64_image = self.preprocess_image(image_data)
            
            # Prepare prompt for Nigerian food classification
            system_prompt = f"""
            You are an expert in Nigerian cuisine. Analyze the provided image and identify any Nigerian foods present.
            
            Guidelines:
            1. Focus specifically on Nigerian dishes and foods
            2. If multiple foods are present, identify all of them
            3. Provide confidence scores for each identification
            4. Include brief descriptions of the dishes identified
            5. If no Nigerian food is detected, clearly state that
            
            Known Nigerian foods include: {', '.join(self.nigerian_foods[:20])}... and many others.
            
            Respond in JSON format with the following structure:
            {{
                "foods_detected": [
                    {{
                        "name": "Food name",
                        "confidence": 0.95,
                        "description": "Brief description",
                        "category": "main_dish/soup/snack/side_dish/drink"
                    }}
                ],
                "is_nigerian_food": true/false,
                "overall_confidence": 0.90,
                "additional_notes": "Any additional observations"
            }}
            """
            
            # Make API call to OpenAI/Azure
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this image and identify any Nigerian foods present."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Extract and parse response
            content = response.choices[0].message.content
            
            # Try to parse JSON response
            try:
                import json
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse JSON response, using fallback")
                return {
                    "foods_detected": [],
                    "is_nigerian_food": False,
                    "overall_confidence": 0.0,
                    "additional_notes": f"Classification completed but response format was unexpected: {content[:200]}..."
                }
                
        except Exception as e:
            logger.error(f"Error in food classification: {str(e)}")
            raise Exception(f"Food classification failed: {str(e)}")

    def get_food_suggestions(self, detected_foods: List[str]) -> List[Dict[str, str]]:
        """
        Get suggestions for similar Nigerian foods based on detected foods.
        
        Args:
            detected_foods: List of detected food names
            
        Returns:
            List of food suggestions with descriptions
        """
        suggestions = []
        
        # Simple mapping of related foods (can be enhanced with ML)
        food_relations = {
            "Jollof Rice": ["Fried Rice", "Coconut Rice", "Ofada Rice"],
            "Egusi Soup": ["Ogbono Soup", "Bitter Leaf Soup", "Afang Soup"],
            "Pounded Yam": ["Amala", "Eba", "Fufu"],
            "Suya": ["Kilishi", "Asun", "Peppered Meat"],
            "Plantain": ["Bole", "Dodo", "Plantain Chips"]
        }
        
        for food in detected_foods:
            if food in food_relations:
                for related_food in food_relations[food]:
                    suggestions.append({
                        "name": related_food,
                        "description": f"Similar to {food}, popular Nigerian dish"
                    })
        
        return suggestions[:5]  # Return top 5 suggestions


# Global classifier instance
food_classifier = FoodClassifier()


def classify_image(image_data: bytes) -> Dict[str, Any]:
    """
    Public function to classify food in an image.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        Dictionary containing classification results
    """
    return food_classifier.classify_food(image_data)


def get_related_foods(detected_foods: List[str]) -> List[Dict[str, str]]:
    """
    Public function to get related food suggestions.
    
    Args:
        detected_foods: List of detected food names
        
    Returns:
        List of related food suggestions
    """
    return food_classifier.get_food_suggestions(detected_foods)
