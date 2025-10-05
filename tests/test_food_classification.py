"""
Test module for food classification functionality.
"""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from PIL import Image
from io import BytesIO
import base64

# Import the main FastAPI app
from main import app
from src.food_classifier.image_classification import FoodClassifier


client = TestClient(app)


class TestFoodClassification:
    """Test cases for food classification endpoints and functionality."""
    
    @pytest.fixture
    def mock_user_token(self):
        """Mock JWT token for authenticated requests."""
        with patch('main.get_current_user') as mock_auth:
            mock_auth.return_value = {
                "username": "testuser",
                "email": "test@example.com",
                "is_verified": True
            }
            yield "mock_token"
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Create a sample image for testing."""
        # Create a simple test image
        image = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        image.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    def test_food_categories_endpoint(self):
        """Test the food categories endpoint."""
        response = client.get("/food-categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert "total_categories" in data
        assert "message" in data
        
        # Check that expected categories are present
        categories = data["categories"]
        expected_categories = ["main_dishes", "soups", "snacks", "side_dishes", "drinks"]
        
        for category in expected_categories:
            assert category in categories
            assert "description" in categories[category]
            assert "examples" in categories[category]
    
    @patch('src.food_classifier.image_classification.classify_image')
    def test_classify_food_success(self, mock_classify, mock_user_token, sample_image_bytes):
        """Test successful food classification."""
        # Mock the classification result
        mock_result = {
            "foods_detected": [
                {
                    "name": "Jollof Rice",
                    "confidence": 0.95,
                    "description": "Popular Nigerian rice dish",
                    "category": "main_dish"
                }
            ],
            "is_nigerian_food": True,
            "overall_confidence": 0.95,
            "additional_notes": "Clear image of Jollof Rice"
        }
        mock_classify.return_value = mock_result
        
        # Prepare file upload
        files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        response = client.post("/classify-food", files=files, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_nigerian_food"] is True
        assert len(data["foods_detected"]) == 1
        assert data["foods_detected"][0]["name"] == "Jollof Rice"
        assert "related_foods" in data
    
    def test_classify_food_invalid_file_type(self, mock_user_token):
        """Test food classification with invalid file type."""
        # Create a non-image file
        text_content = b"This is not an image"
        files = {"file": ("test.txt", text_content, "text/plain")}
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        response = client.post("/classify-food", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]
    
    def test_classify_food_empty_file(self, mock_user_token):
        """Test food classification with empty file."""
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        response = client.post("/classify-food", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "Empty file uploaded" in response.json()["detail"]
    
    def test_classify_food_unauthorized(self, sample_image_bytes):
        """Test food classification without authentication."""
        files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
        
        response = client.post("/classify-food", files=files)
        
        assert response.status_code == 401
    
    @patch('src.food_classifier.image_classification.classify_image')
    def test_classify_food_processing_error(self, mock_classify, mock_user_token, sample_image_bytes):
        """Test food classification with processing error."""
        mock_classify.side_effect = ValueError("Invalid image format")
        
        files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        response = client.post("/classify-food", files=files, headers=headers)
        
        assert response.status_code == 400
        assert "Image processing error" in response.json()["detail"]
    
    @patch('src.food_classifier.image_classification.classify_image')
    def test_classify_food_service_error(self, mock_classify, mock_user_token, sample_image_bytes):
        """Test food classification with service error."""
        mock_classify.side_effect = Exception("API service unavailable")
        
        files = {"file": ("test_image.jpg", sample_image_bytes, "image/jpeg")}
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        response = client.post("/classify-food", files=files, headers=headers)
        
        assert response.status_code == 500
        assert "Classification service error" in response.json()["detail"]


class TestFoodClassifier:
    """Test cases for the FoodClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a FoodClassifier instance for testing."""
        return FoodClassifier()
    
    @pytest.fixture
    def sample_image_bytes(self):
        """Create a sample image for testing."""
        image = Image.new('RGB', (100, 100), color='blue')
        img_buffer = BytesIO()
        image.save(img_buffer, format='JPEG')
        return img_buffer.getvalue()
    
    def test_preprocess_image_success(self, classifier, sample_image_bytes):
        """Test successful image preprocessing."""
        result = classifier.preprocess_image(sample_image_bytes)
        
        assert isinstance(result, str)
        # Check if it's valid base64
        try:
            base64.b64decode(result)
            assert True
        except Exception:
            assert False, "Invalid base64 string"
    
    def test_preprocess_image_invalid_data(self, classifier):
        """Test image preprocessing with invalid data."""
        invalid_data = b"This is not image data"
        
        with pytest.raises(ValueError):
            classifier.preprocess_image(invalid_data)
    
    def test_get_food_suggestions(self, classifier):
        """Test food suggestions functionality."""
        detected_foods = ["Jollof Rice", "Egusi Soup"]
        suggestions = classifier.get_food_suggestions(detected_foods)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5  # Maximum 5 suggestions
        
        for suggestion in suggestions:
            assert "name" in suggestion
            assert "description" in suggestion
    
    def test_get_food_suggestions_no_matches(self, classifier):
        """Test food suggestions with no known foods."""
        detected_foods = ["Unknown Food"]
        suggestions = classifier.get_food_suggestions(detected_foods)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 0
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4o-mini'
    })
    def test_classifier_initialization(self):
        """Test FoodClassifier initialization with environment variables."""
        classifier = FoodClassifier()
        
        assert classifier.model == 'gpt-4o-mini'
        assert len(classifier.nigerian_foods) > 0
        assert "Jollof Rice" in classifier.nigerian_foods
        assert "Egusi Soup" in classifier.nigerian_foods


if __name__ == "__main__":
    pytest.main([__file__])
