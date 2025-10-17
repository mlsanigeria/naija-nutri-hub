import sys
import os
from datetime import datetime, timezone
from bson import ObjectId
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, create_access_token  
from config.database import user_auth
from auth.utils import hash_password

client = TestClient(app)

def add_user():
    user_auth.delete_many({"email": "testuser@example.com"})
    test_user = {
        "_id": ObjectId(),
        "email": "testuser@example.com",
        "username": "testuser",
        "firstname": "Test",
        "lastname": "User",
        "password_hash": hash_password("TestPassword123"),
        "is_verified": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    user_auth.insert_one(test_user)
    print("Test user created successfully!")
    print(f"   - Username: {test_user['username']}")
    print(f"   - Email: {test_user['email']}")
    print(f"   - Password: TestPassword123")

def get_access_token():
    print("Generating access token directly...")
    access_token = create_access_token(data={"sub": "testuser"})
    return access_token

def test_food_classification():
    add_user()
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    image_path = "tests/test.jpg"

    if not os.path.exists(image_path):
        print(f"Warning: Test image not found at {image_path}. Creating a dummy file.")
        with open(image_path, "wb") as f:
            f.write(os.urandom(1024)) 

    print("Sending request to /features/food_classification endpoint...")
    with open(image_path, "rb") as img_file:
        files = {"image": ("test.jpg", img_file, "image/jpeg")}
        response = client.post("/features/food_classification", headers=headers, files=files)
    print(f"Received response with status code: {response.status_code}")
    assert response.status_code == 200
    json_data = response.json()
    print(f"Received JSON response: {json_data}")

    assert "status" in json_data
    assert "inserted_id" in json_data
    assert json_data["status"] == "success"
    assert isinstance(json_data["inserted_id"], str)
    assert len(json_data["inserted_id"]) > 0
    print("Food classification endpoint test passed!")

if __name__ == "__main__":
    test_food_classification()