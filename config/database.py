import os
from pymongo import MongoClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from auth.utils import hash_password  # your hashing function

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
db = client.auth
user_auth = db["user-auth"]     # <-- your users collection
otp_record = db["otp-data"]     # <-- OTP collection (optional)

# Example test user
from bson import ObjectId

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
