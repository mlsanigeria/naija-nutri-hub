from datetime import timezone
from types import SimpleNamespace

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)


class DummyRecipeCollection:
    """In-memory stand-in for the recipe_requests collection."""

    def __init__(self):
        self.inserted_documents = []
        self.inserted_ids = []

    def insert_one(self, document):
        stored_document = document.copy()
        inserted_id = ObjectId()
        self.inserted_documents.append(stored_document)
        self.inserted_ids.append(inserted_id)
        return SimpleNamespace(inserted_id=inserted_id)


@pytest.fixture
def mock_recipe_collection(monkeypatch):
    dummy_collection = DummyRecipeCollection()
    monkeypatch.setattr(main, "recipe_requests", dummy_collection)
    return dummy_collection


def test_recipe_generation_persists_request(mock_recipe_collection):
    payload = {
        "email": "recipe.tester@example.com",
        "food_name": "Jollof Rice",
        "servings": 4,
        "dietary_restrictions": ["vegetarian"],
        "extra_inputs": {"spiciness": "medium"},
    }

    response = client.post("/features/recipe_generation", json=payload)

    assert response.status_code == 200
    body = response.json()

    assert body["message"] == "Recipe request stored successfully."

    stored_request = body["stored_request"]
    assert stored_request["email"] == payload["email"]
    assert stored_request["food_name"] == payload["food_name"]
    assert stored_request["servings"] == payload["servings"]
    assert stored_request["dietary_restrictions"] == payload["dietary_restrictions"]
    assert stored_request["extra_inputs"] == payload["extra_inputs"]
    assert stored_request["timestamp"].endswith("+00:00")

    assert len(mock_recipe_collection.inserted_documents) == 1
    inserted_document = mock_recipe_collection.inserted_documents[0]
    assert inserted_document["email"] == payload["email"]
    assert inserted_document["food_name"] == payload["food_name"]
    assert inserted_document["servings"] == payload["servings"]
    assert inserted_document["dietary_restrictions"] == payload["dietary_restrictions"]
    assert inserted_document["extra_inputs"] == payload["extra_inputs"]
    assert inserted_document["timestamp"].tzinfo is not None
    assert inserted_document["timestamp"].tzinfo == timezone.utc