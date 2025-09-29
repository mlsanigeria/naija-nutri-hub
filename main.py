from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import random
import uuid

app = FastAPI(
    title = "Naija Nutri Hub API",
    description = "Backend API documentation for the Naija Nutri Hub project",
    version = "1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Home
@app.get("/", tags=["Home"])
def index():
    return {"Project": "Naija Nutri Hub"}

# Create new user
@app.post("/create-user", tags=["Authentication"])
def create_user():
  return

# Update user information
@app.put("/update-user/{user_id}", tags=["Authentication"])
def update_user():
  return
