import pytest
from unittest.mock import MagicMock
# Assuming service.py is in the auth directory
from auth.service import user_exists_email, user_exists_username
from bson import ObjectId

# --- Fixture for Mocking MongoDB ---

@pytest.fixture
def mock_user_auth(monkeypatch):
    """Mocks the MongoDB user_auth collection."""
    mock_collection = MagicMock()
    # Replace the actual user_auth imported in auth.service with our mock
    monkeypatch.setattr("auth.service.user_auth", mock_collection)
    return mock_collection

# --- Test Cases for user_exists_email ---

def test_user_exists_email_returns_true(mock_user_auth):
    """
    Test case where a user exists, ensuring case-insensitivity works.
    """
    # Simulate a user found
    mock_user_auth.find_one.return_value = {"_id": ObjectId()}
    
    email = "Test.User@Example.com"
    assert user_exists_email(email) is True
    
    # Crucially, check that the database was queried using the lowercase email
    mock_user_auth.find_one.assert_called_with({"email": email.lower()}, {"_id": 1})

def test_user_exists_email_returns_false(mock_user_auth):
    """
    Test case where no user is found.
    """
    # Simulate no user found
    mock_user_auth.find_one.return_value = None
    
    assert user_exists_email("notfound@example.com") is False

def test_user_exists_email_handles_exception(mock_user_auth, capsys):
    """
    Test case where a database error occurs.
    """
    # Simulate a database error
    mock_user_auth.find_one.side_effect = Exception("DB connection failed")
    
    assert user_exists_email("error@example.com") is False
    
    # Optionally check that an error message was printed
    captured = capsys.readouterr()
    assert "Database error during user_exists_email check: DB connection failed" in captured.out

# --- Test Cases for user_exists_username ---

def test_user_exists_username_returns_true(mock_user_auth):
    """
    Test case where a username exists, checking for exact match query.
    """
    mock_user_auth.find_one.return_value = {"_id": ObjectId()}
    username = "john_doe123"
    
    assert user_exists_username(username) is True
    
    # Check that the database was queried with the exact, case-sensitive username
    mock_user_auth.find_one.assert_called_with({"username": username}, {"_id": 1})

def test_user_exists_username_returns_false(mock_user_auth):
    """
    Test case where no username is found.
    """
    mock_user_auth.find_one.return_value = None
    
    assert user_exists_username("unknown_user") is False

def test_user_exists_username_handles_exception(mock_user_auth):
    """
    Test case where a database error occurs.
    """
    mock_user_auth.find_one.side_effect = Exception("DB timeout")
    
    assert user_exists_username("error_user") is False 