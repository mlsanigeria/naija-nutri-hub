import sys
import os
from datetime import timedelta, datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, create_access_token
from config.database import nutrition_requests, user_auth
from auth.utils import hash_password
from bson import ObjectId

# Create test client
client = TestClient(app)


def setup_test_user():
    """Create a test user for authentication"""
    # Delete existing test user if any
    user_auth.delete_one({"email": "testuser@example.com"})
    
    # Create test user
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
    print("✅ Test user created")
    return test_user


def create_test_token(username="testuser"):
    """Create a JWT token for testing"""
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username}, 
        expires_delta=access_token_expires
    )
    return access_token


def test_nutritional_estimates_basic():
    """Test nutritional estimates endpoint with basic required fields"""
    
    print("\n" + "="*50)
    print("Test 1: Basic Nutrition Request (Required Fields Only)")
    print("="*50)
    
    test_user = setup_test_user()
    token = create_test_token(test_user["username"])
    
    payload = {
        "email": test_user["email"],
        "food_name": "Jollof Rice"  # only required fields
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/features/nutritional_estimates", json=payload, headers=headers)
    
    print(f"📥 Response Status Code: {response.status_code}")
    print(f"📥 Response Body: {response.json()}")
    
    assert response.status_code == 200, "API call failed!"
    inserted_id = response.json().get("inserted_id")
    stored_doc = nutrition_requests.find_one({"_id": ObjectId(inserted_id)})
    
    assert stored_doc['email'] == test_user['email'].lower()
    assert stored_doc['food_name'] == payload['food_name']
    assert stored_doc.get('portion_size') is None
    assert stored_doc.get('extra_inputs') is None
    
    # Cleanup
    nutrition_requests.delete_one({"_id": ObjectId(inserted_id)})
    user_auth.delete_one({"email": test_user['email']})
    print("✅ Test 1 passed\n")
    return True


def test_nutritional_estimates_full():
    """Test nutritional estimates endpoint with all optional fields"""
    
    print("\n" + "="*50)
    print("Test 2: Full Nutrition Request (All Fields)")
    print("="*50)
    
    test_user = setup_test_user()
    token = create_test_token(test_user["username"])
    
    payload = {
        "email": test_user["email"],
        "food_name": "Egusi Soup",
        "portion_size": "2 cups",
        "extra_inputs": {"note": "with pounded yam"}
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/features/nutritional_estimates", json=payload, headers=headers)
    
    print(f"📥 Response Status Code: {response.status_code}")
    print(f"📥 Response Body: {response.json()}")
    
    assert response.status_code == 200, "API call failed!"
    inserted_id = response.json().get("inserted_id")
    stored_doc = nutrition_requests.find_one({"_id": ObjectId(inserted_id)})
    
    assert stored_doc['email'] == test_user['email'].lower()
    assert stored_doc['food_name'] == payload['food_name']
    assert stored_doc['portion_size'] == payload['portion_size']
    assert stored_doc['extra_inputs'] == payload['extra_inputs']
    
    # Cleanup
    nutrition_requests.delete_one({"_id": ObjectId(inserted_id)})
    user_auth.delete_one({"email": test_user['email']})
    print("✅ Test 2 passed\n")
    return True


def test_nutritional_estimates_empty_food_name():
    """Test that empty food name is rejected"""
    
    print("\n" + "="*50)
    print("Test 3: Empty Food Name Validation")
    print("="*50)
    
    test_user = setup_test_user()
    token = create_test_token(test_user["username"])
    
    payload = {
        "email": test_user["email"],
        "food_name": "   "  # empty string
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/features/nutritional_estimates", json=payload, headers=headers)
    
    print(f"📥 Response Status Code: {response.status_code}")
    assert response.status_code == 400, "Empty food_name should return 400"
    
    user_auth.delete_one({"email": test_user['email']})
    print("✅ Test 3 passed\n")
    return True


def test_nutritional_estimates_missing_food_name():
    """Test that missing food_name is rejected"""
    
    print("\n" + "="*50)
    print("Test 4: Missing Food Name Validation")
    print("="*50)
    
    test_user = setup_test_user()
    token = create_test_token(test_user["username"])
    
    payload = {
        "email": test_user["email"],
        "portion_size": "1 cup"  # missing food_name
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/features/nutritional_estimates", json=payload, headers=headers)
    
    print(f"📥 Response Status Code: {response.status_code}")
    assert response.status_code == 422, "Missing food_name should return 422"
    
    user_auth.delete_one({"email": test_user['email']})
    print("✅ Test 4 passed\n")
    return True


def test_nutritional_estimates_without_auth():
    """Test that endpoint requires authentication"""
    
    print("\n" + "="*50)
    print("Test 5: Authentication Required")
    print("="*50)
    
    payload = {
        "email": "unauth@example.com",
        "food_name": "Suya"
    }
    
    response = client.post("/features/nutritional_estimates", json=payload)
    print(f"📥 Response Status Code: {response.status_code}")
    assert response.status_code == 401, "Request without token should return 401"
    print("✅ Test 5 passed\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" NUTRITIONAL ESTIMATES ENDPOINT TEST SUITE")
    print("="*60)
    
    test1_passed = test_nutritional_estimates_basic()
    test2_passed = test_nutritional_estimates_full()
    test3_passed = test_nutritional_estimates_empty_food_name()
    test4_passed = test_nutritional_estimates_missing_food_name()
    test5_passed = test_nutritional_estimates_without_auth()
    
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (Basic Request - Required Fields): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Full Request - All Fields): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 (Empty Food Name Validation): {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    print(f"Test 4 (Missing Food Name Validation): {'✅ PASSED' if test4_passed else '❌ FAILED'}")
    print(f"Test 5 (Authentication Required): {'✅ PASSED' if test5_passed else '❌ FAILED'}")
    print("="*60)
    
    all_passed = all([test1_passed, test2_passed, test3_passed, test4_passed, test5_passed])
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print("\n⚠️ SOME TESTS FAILED")
