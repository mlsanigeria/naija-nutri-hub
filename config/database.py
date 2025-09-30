import os
from pymongo import MongoClient

# Get Configuration Settings
from dotenv import load_dotenv
load_dotenv()

client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))

db = client.auth
user_auth = db["user-auth"]
otp_record = db["otp-data"]
