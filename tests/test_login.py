import pytest
from auth.utils import hash_password, verify_password

# Mock user data
user_db_mock = {
    "username": "testuser",
    "email": "test@example.com",
    "password_hash": hash_password("testpass"),
    "is_verified": True
}

def test_verify_password_success():
    assert verify_password("testpass", user_db_mock["password_hash"]) is True

def test_verify_password_fail():
    assert verify_password("wrongpass", user_db_mock["password_hash"]) is False
