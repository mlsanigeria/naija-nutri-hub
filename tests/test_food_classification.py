import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.database import user_auth
from auth.utils import hash_password
from datetime import datetime, timezone
from bson import ObjectId
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

def add_user():
    
    
    user_auth.delete_many({"email": "testuser@example.com"})
    test_user = {
        "_id": ObjectId(),
        "email": "testuser@example.com",
        "username": "testuser",
        "firstname": "Test",
        "lastname": "User",
        "password_hash": hash_password("TestPassword123"),  # Note: field is password_hash, not password
        "is_verified": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    user_auth.insert_one(test_user)
    print("✅ Test user created successfully!")
    print(f"Username: {test_user['username']}")
    print(f"Email: {test_user['email']}")
    print(f"Name: {test_user['firstname']} {test_user['lastname']}")
    print(f"Password: TestPassword123")
    print(f"Verified: {test_user['is_verified']}")



def get_access_token():
    response = client.post(
       "/login",  # update with your actual login route path
        data={
            "username": "testuser",
            "password": "TestPassword123"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    json_resp = response.json()
    return json_resp["access_token"]  
    
def test_food_classification():
    add_user()
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    image_path = "tests/sample.jpg"
    
    with open(image_path, "rb") as img_file:
        files = {"image": ("sample.jpg", img_file, "image/jpeg")}
        response = client.post("/features/food_classification", headers=headers, files=files)
    
    assert response.status_code == 200
    json_data = response.json()
    assert "message" in json_data and json_data["message"] == "Request saved successfully"
    assert "request_id" in json_data

        

        
