# test_user_existence.py
import pytest
from unittest.mock import MagicMock
from auth.service import user_exists_email, user_exists_username

# Mocking the user_auth collection
@pytest.fixture
def mock_user_auth(monkeypatch):
    mock_collection = MagicMock()
    monkeypatch.setattr("auth.service.user_auth", mock_collection)
    return mock_collection

# ------------------------------
# Test cases for user_exists_email
# ------------------------------
def test_user_exists_email_returns_true(mock_user_auth):
    # Simulate that a user exists
    mock_user_auth.find_one.return_value = {"_id": "123"}
    assert user_exists_email("test@example.com") is True
    mock_user_auth.find_one.assert_called_with({"email": "test@example.com"}, {"_id": 1})

def test_user_exists_email_returns_false(mock_user_auth):
    # Simulate no user found
    mock_user_auth.find_one.return_value = None
    assert user_exists_email("notfound@example.com") is False

def test_user_exists_email_handles_exception(mock_user_auth):
    # Simulate database error
    mock_user_auth.find_one.side_effect = Exception("DB error")
    assert user_exists_email("error@example.com") is False

# ------------------------------
# Test cases for user_exists_username
# ------------------------------
def test_user_exists_username_returns_true(mock_user_auth):
    mock_user_auth.find_one.return_value = {"_id": "123"}
    assert user_exists_username("john_doe") is True
    mock_user_auth.find_one.assert_called_with({"username": "john_doe"}, {"_id": 1})

def test_user_exists_username_returns_false(mock_user_auth):
    mock_user_auth.find_one.return_value = None
    assert user_exists_username("unknown_user") is False

def test_user_exists_username_handles_exception(mock_user_auth):
    mock_user_auth.find_one.side_effect = Exception("DB error")
    assert user_exists_username("error_user") is False
