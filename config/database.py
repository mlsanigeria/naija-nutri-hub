import os
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from auth.utils import hash_password  # your hashing function

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"), tz_aware=True, tzinfo=timezone.utc)

# Auth DB
auth_db = client.auth
user_auth = auth_db["user-auth"]     # <-- Authentication collection
otp_record = auth_db["otp-data"]     # <-- OTP collection

# Feature DB
feature_db = client.features
classification_requests = feature_db["classification_requests"]
recipe_requests = feature_db["recipe_requests"]
nutrition_requests = feature_db["nutrition_requests"]
purchase_loc_requests = feature_db["purchase_loc_requests"]

# Example test user
from bson import ObjectId


"""
test_user = {
    "_id": ObjectId(),  # explicitly generate ObjectId
    "email": "testuser@example.com",
    "name": "Test User",
    "password": hash_password("TestPassword123"),
    "created_at": datetime.now(timezone.utc)
}


# Insert user
user_auth.insert_one(test_user)
print("Test user inserted!")
"""