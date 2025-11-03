"""
Test suite for enhanced recipe generation with additional input fields.

Tests verify that the recipe generation feature correctly handles:
- servings (Optional[float])
- dietary_restriction (Optional[List[str]])
- extra_inputs (Optional[str])
"""

from datetime import timezone
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

import main


def mock_get_current_user():
    """Mock implementation of get_current_user for testing."""
    return {"username": "testuser", "email": "test@example.com"}


# Override the dependency
app = main.app
app.dependency_overrides[main.get_current_user] = mock_get_current_user

client = TestClient(app)


class DummyRecipeCollection:
    """In-memory stand-in for the recipe_requests collection."""

    def __init__(self):
        self.inserted_documents = []
        self.inserted_ids = []

    def insert_one(self, document):
        stored_document = document.copy()
        inserted_id = ObjectId()
        self.inserted_documents.append(stored_document)
        self.inserted_ids.append(inserted_id)
        return SimpleNamespace(inserted_id=inserted_id)


@pytest.fixture
def mock_recipe_collection(monkeypatch):
    dummy_collection = DummyRecipeCollection()
    monkeypatch.setattr(main, "recipe_requests", dummy_collection)
    return dummy_collection


class TestRecipeGenerationWithServings:
    """Test recipe generation with servings parameter."""
    
    def test_recipe_generation_with_servings(self, mock_recipe_collection):
        """Test that servings parameter is properly passed through the generation flow."""
        payload = {
            "email": "test.user@example.com",
            "food_name": "Jollof Rice",
            "servings": 6,
            "dietary_restriction": None,
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Jollof Rice",
                "servings": 6,
                "description": "A delicious one-pot rice dish",
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            # Verify the endpoint was called with the correct parameters
            assert response.status_code == 200
            mock_recipe.assert_called_once()
            call_args = mock_recipe.call_args
            
            assert call_args.kwargs.get('food_name') == "Jollof Rice"
            assert call_args.kwargs.get('servings') == 6
            assert call_args.kwargs.get('dietary_restriction') is None
            assert call_args.kwargs.get('extra_inputs') is None


class TestRecipeGenerationWithDietaryRestrictions:
    """Test recipe generation with dietary restrictions parameter."""
    
    def test_recipe_generation_with_single_dietary_restriction(self, mock_recipe_collection):
        """Test with a single dietary restriction."""
        payload = {
            "email": "test.user@example.com",
            "food_name": "Egusi Soup",
            "servings": None,
            "dietary_restriction": ["Vegetarian"],
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Egusi Soup",
                "dietary_restrictions": ["Vegetarian"],
                "description": "A vegetarian version of egusi soup",
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            mock_recipe.assert_called_once()
            call_args = mock_recipe.call_args
            
            assert call_args.kwargs.get('dietary_restriction') == ["Vegetarian"]
    
    def test_recipe_generation_with_multiple_dietary_restrictions(self, mock_recipe_collection):
        """Test with multiple dietary restrictions."""
        payload = {
            "email": "test.user@example.com",
            "food_name": "Pounded Yam",
            "servings": 4,
            "dietary_restriction": ["Vegetarian", "Gluten-free", "Nut allergy"],
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Pounded Yam",
                "servings": 4,
                "dietary_restrictions": ["Vegetarian", "Gluten-free", "Nut allergy"],
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            mock_recipe.assert_called_once()
            call_args = mock_recipe.call_args
            
            assert call_args.kwargs.get('dietary_restriction') == ["Vegetarian", "Gluten-free", "Nut allergy"]


class TestRecipeGenerationWithExtraInputs:
    """Test recipe generation with extra_inputs parameter."""
    
    def test_recipe_generation_with_cuisine_preference(self, mock_recipe_collection):
        """Test with cuisine preference in extra_inputs."""
        payload = {
            "email": "test.user@example.com",
            "food_name": "Moi Moi",
            "servings": None,
            "dietary_restriction": None,
            "extra_inputs": "Preferred Cuisine: Yoruba, Traditional method",
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Moi Moi",
                "description": "Traditional Yoruba steamed bean pudding",
                "user_preferences": "Preferred Cuisine: Yoruba, Traditional method",
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            mock_recipe.assert_called_once()
            call_args = mock_recipe.call_args
            
            assert call_args.kwargs.get('extra_inputs') == "Preferred Cuisine: Yoruba, Traditional method"


class TestRecipeGenerationWithAllParameters:
    """Test recipe generation with all parameters provided."""
    
    def test_recipe_generation_with_all_fields(self, mock_recipe_collection):
        """Test that all input fields are properly integrated into recipe generation."""
        payload = {
            "email": "chef@example.com",
            "food_name": "Pepper Rice",
            "servings": 8,
            "dietary_restriction": ["Halal", "Gluten-free"],
            "extra_inputs": "Preferred Cuisine: Hausa, Spicy level: Medium",
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Pepper Rice",
                "servings": 8,
                "spice_level": "Medium",
                "dietary_restrictions": ["Halal", "Gluten-free"],
                "user_preferences": "Preferred Cuisine: Hausa, Spicy level: Medium",
                "region": "Hausa",
                "ingredients": [
                    {"name": "Rice", "quantity": "4 cups", "notes": "parboiled"},
                    {"name": "Red peppers", "quantity": "4 large", "notes": "blended"},
                ],
                "steps": [
                    {"step_number": 1, "instruction": "Fry the peppers"},
                    {"step_number": 2, "instruction": "Add rice and cook"},
                ],
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            body = response.json()
            
            # Verify all parameters were passed to the generation function
            mock_recipe.assert_called_once()
            call_args = mock_recipe.call_args
            
            assert call_args.kwargs.get('food_name') == "Pepper Rice"
            assert call_args.kwargs.get('servings') == 8
            assert call_args.kwargs.get('dietary_restriction') == ["Halal", "Gluten-free"]
            assert call_args.kwargs.get('extra_inputs') == "Preferred Cuisine: Hausa, Spicy level: Medium"
            
            # Verify the generated recipe includes user preferences
            generated_recipe = body["generated_recipe"]
            assert generated_recipe["servings"] == 8
            assert "Halal" in generated_recipe["dietary_restrictions"]
            assert "Gluten-free" in generated_recipe["dietary_restrictions"]
            assert "Hausa" in generated_recipe["user_preferences"]


class TestRecipeGenerationEdgeCases:
    """Test edge cases and error handling."""
    
    def test_recipe_generation_with_zero_servings(self, mock_recipe_collection):
        """Test that zero servings is handled correctly."""
        payload = {
            "email": "test@example.com",
            "food_name": "Okra Soup",
            "servings": 0,
            "dietary_restriction": None,
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {"food_name": "Okra Soup"}
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            call_args = mock_recipe.call_args
            assert call_args.kwargs.get('servings') == 0
    
    def test_recipe_generation_with_fractional_servings(self, mock_recipe_collection):
        """Test that fractional servings are handled correctly."""
        payload = {
            "email": "test@example.com",
            "food_name": "Garri and Soup",
            "servings": 2.5,
            "dietary_restriction": None,
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {"food_name": "Garri and Soup", "servings": 2.5}
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            call_args = mock_recipe.call_args
            assert call_args.kwargs.get('servings') == 2.5
    
    def test_recipe_generation_with_empty_dietary_list(self, mock_recipe_collection):
        """Test with an empty dietary restriction list."""
        payload = {
            "email": "test@example.com",
            "food_name": "Fufu",
            "servings": None,
            "dietary_restriction": [],
            "extra_inputs": None,
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {"food_name": "Fufu"}
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            call_args = mock_recipe.call_args
            assert call_args.kwargs.get('dietary_restriction') == []


class TestRecipeGenerationPersistence:
    """Test that recipe requests are properly persisted with all fields."""
    
    def test_recipe_request_persisted_with_all_fields(self, mock_recipe_collection):
        """Test that all recipe request fields are stored in the database."""
        payload = {
            "email": "persistent.user@example.com",
            "food_name": "Suya",
            "servings": 2,
            "dietary_restriction": ["Vegan", "Diabetic"],
            "extra_inputs": "Less spicy, no nuts",
        }

        with patch('main.get_recipe_for_dish') as mock_recipe:
            mock_recipe.return_value = {
                "food_name": "Suya",
                "servings": 2,
                "dietary_restrictions": ["Vegan", "Diabetic"],
            }
            
            response = client.post("/features/recipe_generation", json=payload)

            assert response.status_code == 200
            
            # Verify the document was inserted with all fields
            assert len(mock_recipe_collection.inserted_documents) == 1
            inserted_doc = mock_recipe_collection.inserted_documents[0]
            
            assert inserted_doc["email"] == "persistent.user@example.com"
            assert inserted_doc["food_name"] == "Suya"
            assert inserted_doc["servings"] == 2
            assert inserted_doc["dietary_restriction"] == ["Vegan", "Diabetic"]
            assert inserted_doc["extra_inputs"] == "Less spicy, no nuts"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
