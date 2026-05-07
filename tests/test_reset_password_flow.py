from datetime import datetime, timezone
from types import SimpleNamespace

from bson import ObjectId
from fastapi.testclient import TestClient

import auth.service as auth_service
import main
from auth.utils import hash_password


client = TestClient(main.app)


class DummyCollection:
    def __init__(self, documents=None):
        self.documents = list(documents or [])

    def _matches(self, document, query):
        for key, expected in query.items():
            value = document.get(key)
            if isinstance(expected, dict) and "$regex" in expected:
                if str(value).lower() != str(expected["$regex"]).strip("^$").lower():
                    return False
            elif value != expected:
                return False
        return True

    def find_one(self, query, sort=None):
        matches = [doc for doc in self.documents if self._matches(doc, query)]
        if sort and matches:
            field, direction = sort[0]
            reverse = direction < 0
            matches.sort(key=lambda item: item.get(field), reverse=reverse)
        return matches[0] if matches else None

    def update_one(self, query, update):
        document = self.find_one(query)
        if not document:
            return SimpleNamespace(modified_count=0)
        for key, value in update.get("$set", {}).items():
            document[key] = value
        return SimpleNamespace(modified_count=1)

    def delete_many(self, query):
        remaining = [doc for doc in self.documents if not self._matches(doc, query)]
        deleted_count = len(self.documents) - len(remaining)
        self.documents = remaining
        return SimpleNamespace(deleted_count=deleted_count)


def test_reset_password_verifies_account_and_allows_login(monkeypatch):
    user_doc = {
        "_id": ObjectId(),
        "email": "resetuser@example.com",
        "firstname": "Reset",
        "lastname": "User",
        "username": "resetuser",
        "password_hash": hash_password("OldPassword123!"),
        "is_verified": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "last_used": datetime.now(timezone.utc),
    }
    otp_doc = {
        "_id": ObjectId(),
        "email": "resetuser@example.com",
        "otp": "123456",
        "created_at": datetime.now(timezone.utc),
    }

    user_collection = DummyCollection([user_doc])
    otp_collection = DummyCollection([otp_doc])

    monkeypatch.setattr(main, "user_auth", user_collection)
    monkeypatch.setattr(main, "otp_record", otp_collection)
    monkeypatch.setattr(auth_service, "user_auth", user_collection)
    monkeypatch.setattr(auth_service, "otp_record", otp_collection)
    monkeypatch.setattr(
        main,
        "send_email_reset_password_success",
        lambda user_firstname, receiver: {
            "status": "success",
            "message": f"Email sent to {receiver}",
        },
    )

    verify_response = client.post(
        "/verify_reset_otp",
        json={"email": "resetuser@example.com", "otp": "123456"},
    )
    assert verify_response.status_code == 200
    assert "OTP verified successfully" in verify_response.json()["message"]

    reset_response = client.post(
        "/reset_password",
        json={
            "email": "resetuser@example.com",
            "new_password": "NewPassword123!",
        },
    )
    assert reset_response.status_code == 200
    assert reset_response.json()["account_verified"] is True
    assert user_doc["is_verified"] is True

    login_response = client.post(
        "/login",
        data={
            "username": "resetuser@example.com",
            "password": "NewPassword123!",
            "grant_type": "password",
        },
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
