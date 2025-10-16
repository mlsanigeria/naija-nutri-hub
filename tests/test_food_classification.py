import sys
import os
from datetime import timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app, create_access_token
from config.database import classification_requests, user_auth
from auth.utils import hash_password
from datetime import datetime, timezone
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


def test_food_classification_endpoint():
    """Test the food classification endpoint"""
    
    # Setup
    print("\n" + "="*50)
    print("Testing Food Classification Endpoint")
    print("="*50)
    
    # Create test user
    test_user = setup_test_user()
    
    # Create authentication token
    token = create_test_token(test_user["username"])
    print(f"✅ Token created: {token[:20]}...")
    
    # Prepare image file path
    image_path = os.path.join(os.path.dirname(__file__), "sample.jpg")
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ ERROR: sample.jpg not found at {image_path}")
        print("Please create a sample.jpg file in the tests folder")
        return False
    
    print(f"✅ Image found: {image_path}")
    print(f"   Image size: {os.path.getsize(image_path)} bytes")
    
    # Make request to classification endpoint
    with open(image_path, "rb") as image_file:
        files = {"image": ("sample.jpg", image_file, "image/jpeg")}
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\n📤 Making POST request to /features/food_classification")
        response = client.post(
            "/features/food_classification",
            files=files,
            headers=headers
        )
    
    # Check response
    print(f"\n📥 Response Status Code: {response.status_code}")
    print(f"📥 Response Body: {response.json()}")
    
    if response.status_code == 200:
        print("✅ API call successful!")
        
        # Verify data in database
        response_data = response.json()
        request_id = response_data.get("request_id")
        
        if request_id:
            print(f"\n🔍 Verifying data in MongoDB...")
            print(f"   Request ID: {request_id}")
            
            # Fetch from database
            stored_doc = classification_requests.find_one({"_id": ObjectId(request_id)})
            
            if stored_doc:
                print("✅ Document found in database!")
                print(f"   Email: {stored_doc['email']}")
                print(f"   Timestamp: {stored_doc['timestamp']}")
                print(f"   Image size: {len(stored_doc['image'])} bytes")
                print(f"   Image type: {type(stored_doc['image'])}")
                
                # Verify schema
                assert stored_doc['email'] == test_user['email'], "Email mismatch!"
                assert 'image' in stored_doc, "Image not stored!"
                assert 'timestamp' in stored_doc, "Timestamp not stored!"
                assert len(stored_doc['image']) > 0, "Image data is empty!"
                
                print("\n✅ All verifications passed!")
                print("="*50)
                
                # Cleanup
                classification_requests.delete_one({"_id": ObjectId(request_id)})
                user_auth.delete_one({"email": test_user['email']})
                print("🧹 Cleanup completed")
                
                return True
            else:
                print("❌ Document not found in database!")
                return False
    else:
        print(f"❌ API call failed!")
        print(f"   Error: {response.json().get('detail', 'Unknown error')}")
        return False


def test_classification_without_auth():
    """Test that endpoint requires authentication"""
    print("\n" + "="*50)
    print("Testing Authentication Required")
    print("="*50)
    
    image_path = os.path.join(os.path.dirname(__file__), "sample.jpg")
    
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            files = {"image": ("sample.jpg", image_file, "image/jpeg")}
            
            print("📤 Making request WITHOUT authentication token")
            response = client.post("/features/food_classification", files=files)
            
            print(f"📥 Response Status Code: {response.status_code}")
            
            if response.status_code == 401:
                print("✅ Correctly rejected unauthorized request!")
                return True
            else:
                print("❌ Should have returned 401 Unauthorized!")
                return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" FOOD CLASSIFICATION ENDPOINT TEST SUITE")
    print("="*60)
    
    # Run tests
    test1_passed = test_food_classification_endpoint()
    test2_passed = test_classification_without_auth()
    
    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (Successful Classification): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Authentication Required): {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print("="*60)
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print("\n⚠️  SOME TESTS FAILED")