import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from unittest.mock import MagicMock, patch
from datetime import datetime
import uuid

# --- 1. MOCK DEPENDENCIES ---
# Define a placeholder for the Pydantic model used in the route
class RecipePayload(BaseModel):
    food_name: str
    optional_detail: str | None = None
    
# Mock data for a successful recipe generation (with the new image_url field)
# NOTE: The image_url is fully mockable since the actual generation logic is bypassed.
MOCK_SUCCESS_RECIPE = {
    "title": "Mock Tofu Stir Fry",
    "ingredients": ["tofu", "soy sauce", "vegetables"],
    "steps": [
        {"step_number": 1, "instruction": "Slice the tofu.", "image_url": "http://mock.url/slice.png"},
        {"step_number": 2, "instruction": "Stir fry vegetables.", "image_url": "http://mock.url/fry.png"},
    ],
    "source": "mocked_data"
}

# Mock function for get_current_user
def mock_get_current_user_success():
    # Provides a valid user dictionary to simulate successful authentication
    return {"user_id": str(uuid.uuid4()), "email": "test@example.com"}

# Mock database collection object (MongoDB collection)
# Mocking the insert_one method to return a successful result
mock_inserted_id = str(uuid.uuid4())
mock_recipe_requests = MagicMock()
mock_recipe_requests.insert_one.return_value = MagicMock(inserted_id=mock_inserted_id)

# --- 2. SETUP MOCK APPLICATION ---

# Instantiate a mock application
app = FastAPI()

# Placeholder for the actual function being imported and tested
def get_recipe_for_dish(food_name: str):
    """Placeholder for the function being mocked."""
    raise NotImplementedError("This function should be mocked during testing.")


# Replicate the original route logic using the mock objects
@app.post("/features/recipe_generation", tags=["Features"])
async def recipe_generation(
    recipe_data: RecipePayload, 
    # Directly using the successful mock for simplicity in this test file
    current_user: dict = Depends(mock_get_current_user_success) 
):
    """
    Accepts food name and other optional details, returns recipe suggestions
    """
    # Validate authentication
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Input validation
    if not recipe_data.food_name or not recipe_data.food_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Food name is required and cannot be empty"
        )
    
    # Main Implementation (with function calls)
    try:
        # Calls the function that is mocked in the tests below
        generated_recipe = get_recipe_for_dish(recipe_data.food_name.strip()) 
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {exc}")
    
    if not generated_recipe:
        raise HTTPException(status_code=404, detail="Unable to generate recipe for the requested dish.")
        
    # Store request in DB
    try:
        request_document = recipe_data.model_dump(exclude_none=True)
        # Adding mock timestamp for storage
        request_document["timestamp"] = datetime.now() 
        result = mock_recipe_requests.insert_one(request_document)
    except Exception as exc:
        # The correct exception handling for a DB failure
        raise HTTPException(status_code=500, detail=f"Failed to store recipe request: {exc}")
        
    request_document.pop("_id", None)

    request_document["user_email"] = current_user.get("email")
    request_document["generated_recipe"] = generated_recipe

    return {
        "message": "Recipe request stored successfully.",
        "food_name": recipe_data.food_name.strip(),
        "generated_recipe": generated_recipe,
        "request_metadata": {
            "timestamp": request_document["timestamp"].isoformat() if "timestamp" in request_document else None,
            "user_email": request_document.get("user_email"),
            "request_id": str(result.inserted_id),
        },
    }

# Create a test client
client = TestClient(app)

# --- 3. PYTEST TEST FUNCTIONS ---

# Use patch to replace the actual get_recipe_for_dish function with a mock
@patch(__name__ + '.get_recipe_for_dish', MagicMock(return_value=MOCK_SUCCESS_RECIPE))
@patch(__name__ + '.mock_recipe_requests', mock_recipe_requests)
def test_successful_recipe_generation(): # Argument removed to fix ERROR
    """Tests the route with a successful recipe and image generation."""
    
    # Reset mock call count before test
    mock_recipe_requests.insert_one.reset_mock()
    
    # Simulate the request data
    recipe_data = {"food_name": "Tofu Stir Fry", "optional_detail": "Quick and simple"}
    
    response = client.post(
        "/features/recipe_generation", 
        json=recipe_data
    )
    
    assert response.status_code == 200
    response_json = response.json()
    
    # Check if the mock recipe data (with image_url) is in the response
    assert response_json["generated_recipe"] == MOCK_SUCCESS_RECIPE
    
    # Verify that the new image_url field is present in the response
    assert "image_url" in response_json["generated_recipe"]["steps"][0]
    # Check the actual mock URL value
    assert response_json["generated_recipe"]["steps"][0]["image_url"] == "http://mock.url/slice.png"
    
    # Verify that the DB insert was called exactly once
    mock_recipe_requests.insert_one.assert_called_once()
    
    # Verify metadata fields are present
    assert "request_id" in response_json["request_metadata"]
    assert response_json["request_metadata"]["user_email"] == "test@example.com"


@patch(__name__ + '.get_recipe_for_dish', MagicMock(return_value=None))
def test_recipe_not_found():
    """Tests the case where recipe generation fails (404)."""
    recipe_data = {"food_name": "NonExistentDish"}
    
    response = client.post(
        "/features/recipe_generation", 
        json=recipe_data
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Unable to generate recipe for the requested dish."


def test_missing_food_name():
    """Tests the case where the required food_name field is missing (400)."""
    recipe_data_empty = {"food_name": ""}
    response_empty = client.post("/features/recipe_generation", json=recipe_data_empty)
    assert response_empty.status_code == 400
    
    recipe_data_whitespace = {"food_name": "   "}
    response_whitespace = client.post("/features/recipe_generation", json=recipe_data_whitespace)
    assert response_whitespace.status_code == 400

    expected_detail = "Food name is required and cannot be empty"
    assert response_empty.json()["detail"] == expected_detail
    assert response_whitespace.json()["detail"] == expected_detail


@patch(__name__ + '.get_recipe_for_dish', MagicMock(side_effect=Exception("API Error during generation")))
def test_internal_server_error_during_generation():
    """Tests the case where an unexpected exception occurs during generation (500)."""
    recipe_data = {"food_name": "ErrorDish"}
    
    response = client.post(
        "/features/recipe_generation", 
        json=recipe_data
    )
    
    assert response.status_code == 500
    assert "Recipe generation failed: API Error during generation" in response.json()["detail"]

@patch(__name__ + '.get_recipe_for_dish', MagicMock(return_value=MOCK_SUCCESS_RECIPE))
def test_internal_server_error_during_db_storage():
    """Tests the case where DB storage fails after successful recipe generation (500)."""
    recipe_data = {"food_name": "DBFailDish"}
    
    with patch.object(mock_recipe_requests, 'insert_one', side_effect=Exception("DB connection error")):
        response = client.post(
            "/features/recipe_generation", 
            json=recipe_data
        )
    
    assert response.status_code == 500
    assert "Failed to store recipe request: DB connection error" in response.json()["detail"]
