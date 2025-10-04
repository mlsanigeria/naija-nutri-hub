import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from config.database import user_auth, otp_record
from main import app
from auth.utils import hash_password

client = TestClient(app)

@pytest.fixture
def sample_user():
    """Create a test unverified user"""
    # user_id = ObjectId()
    test_user = {
    # "_id": user_id,  
    "email": "testuser@example.com",
    "firstname": "Test",
    "lastname": "User",
    "username": "testuser",
    "password": hash_password("TestPassword123"),
    "created_at": datetime.now(timezone.utc)
    }

    user_auth.insert_one(test_user)
    yield test_user
    # Cleanup
    user_auth.delete_one({"email": test_user["email"]})


@pytest.fixture
def valid_otp(sample_user):
    """Create a valid OTP for the test user"""

    otp = {
        "_id": ObjectId(),
        "email": sample_user["email"],
        "otp": "123456",
        "created_at": datetime.now(timezone.utc)
    }
    otp_record.insert_one(otp)
    yield otp
    # Cleanup
    otp_record.delete_many({"email": sample_user["email"]})


def test_verify_with_valid_otp(sample_user, valid_otp):
    """Test successful OTP verification"""
    response = client.post("/verify", json={
        "email": sample_user["email"],
        "otp": valid_otp["otp"]
    })
    
    assert response.status_code == 200
    assert response.json()["message"] == "Account verified successfully"
    
    # Verify user is marked as verified in DB
    user = user_auth.find_one({"email": sample_user["email"]})
    assert user["is_verified"] is True


def test_verify_with_incorrect_otp(sample_user):
    """Test verification with wrong OTP"""

    response = client.post("/verify", json={
        "email": sample_user["email"],
        "otp": "999999"
    })
    
    assert response.status_code == 400
    assert "Incorrect OTP" in response.json()["detail"]


def test_verify_with_expired_otp(sample_user):
    """Test verification with expired OTP"""

    expired_otp = {
        "email": sample_user["email"],
        "otp": "123456",
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=15)
    }
    otp_record.insert_one(expired_otp)
    
    response = client.post("/verify", json={
        "email": sample_user["email"],
        "otp": "123456"
    })
    
    assert response.status_code == 400
    assert "expired" in response.json()["detail"].lower()
    
    # Cleanup
    otp_record.delete_many({"email": sample_user["email"]})


def test_verify_nonexistent_user():
    """Test verification for user that doesn't exist"""
    response = client.post("/verify", json={
        "email": "nonexistent@example.com",
        "otp": "123456"
    })
    
    assert response.status_code == 400
    assert "Incorrect OTP" in response.json()["detail"]


def test_otp_is_deleted_after_use(sample_user, valid_otp):
    """Test that OTP is deleted after successful verification"""
    client.post("/verify", json={
        "email": sample_user["email"],
        "otp": valid_otp["otp"]
    })
    
    # Check OTP is deleted
    otp = otp_record.find_one({"email": sample_user["email"]})
    assert otp is None