from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo.errors import DuplicateKeyError

from src.core.config import INITIAL_CREDITS
from src.core.database import get_database
from src.core.security import hash_password, verify_password


class UserService:
    def __init__(self):
        self.db = None
        self.users = None
        self._indexes_ready = False

    def _ensure_collection(self):
        if self.db is None:
            self.db = get_database()
            self.users = self.db.users
        if not self._indexes_ready:
            self.users.create_index("user_id", unique=True)
            self.users.create_index("email", unique=True, sparse=True)
            self._indexes_ready = True

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _serialize_user(self, user: dict[str, Any]) -> dict[str, Any]:
        user["id"] = str(user.pop("_id"))
        if "password_hash" in user:
            user.pop("password_hash", None)
        return user

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        self._ensure_collection()
        user = self.users.find_one({"user_id": user_id})
        if not user:
            return None
        return self._serialize_user(user)

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        self._ensure_collection()
        user = self.users.find_one({"email": self._normalize_email(email)})
        if not user:
            return None
        return self._serialize_user(user)

    def create_user(self, *, name: str, email: str, password: str) -> dict[str, Any]:
        self._ensure_collection()
        normalized_email = self._normalize_email(email)
        user_doc = {
            "user_id": str(uuid4()),
            "name": name.strip(),
            "email": normalized_email,
            "password_hash": hash_password(password),
            "credits": INITIAL_CREDITS,
            "plan_status": "free",
            "token_version": 0,
            "is_active": True,
            "created_at": self._now(),
            "updated_at": self._now(),
            "last_login_at": None,
        }
        try:
            inserted = self.users.insert_one(user_doc)
        except DuplicateKeyError as exc:
            raise ValueError("An account with this email already exists") from exc
        user = self.users.find_one({"_id": inserted.inserted_id})
        return self._serialize_user(user)

    def authenticate(self, *, email: str, password: str) -> dict[str, Any]:
        self._ensure_collection()
        user = self.users.find_one({"email": self._normalize_email(email)})
        if not user:
            raise ValueError("Invalid email or password")
        if not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid email or password")
        self.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login_at": self._now(), "updated_at": self._now()}},
        )
        user = self.users.find_one({"_id": user["_id"]})
        return self._serialize_user(user)

    def update_profile(self, user_id: str, *, name: str | None = None) -> dict[str, Any]:
        self._ensure_collection()
        updates: dict[str, Any] = {"updated_at": self._now()}
        if name is not None:
            updates["name"] = name.strip()
        self.users.update_one({"user_id": user_id}, {"$set": updates})
        user = self.users.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")
        return self._serialize_user(user)

    def change_password(
        self,
        user_id: str,
        *,
        current_password: str,
        new_password: str,
    ) -> None:
        self._ensure_collection()
        user = self.users.find_one({"user_id": user_id})
        if not user or not verify_password(current_password, user.get("password_hash", "")):
            raise ValueError("Current password is incorrect")
        self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "updated_at": self._now(),
                },
                "$inc": {"token_version": 1},
            },
        )

    def update_billing_status(
        self,
        user_id: str,
        *,
        plan_status: str | None = None,
        subscription_status: str | None = None,
        plan_code: str | None = None,
        subscription_id: str | None = None,
    ) -> None:
        self._ensure_collection()
        updates: dict[str, Any] = {"updated_at": self._now()}
        if plan_status is not None:
            updates["plan_status"] = plan_status
        if subscription_status is not None:
            updates["subscription_status"] = subscription_status
        if plan_code is not None:
            updates["plan_code"] = plan_code
        if subscription_id is not None:
            updates["subscription_id"] = subscription_id
        self.users.update_one({"user_id": user_id}, {"$set": updates})

    def disable_user(self, user_id: str) -> dict[str, Any]:
        self._ensure_collection()
        result = self.users.find_one_and_update(
            {"user_id": user_id},
            {
                "$set": {"is_active": False, "updated_at": self._now()},
                "$inc": {"token_version": 1},
            },
        )
        if not result:
            raise ValueError("User not found")
        return self._serialize_user(result)

    def ensure_legacy_user(
        self,
        user_id: str,
        *,
        credits: int | None = None,
    ) -> dict[str, Any]:
        self._ensure_collection()
        user = self.users.find_one({"user_id": user_id})
        if user:
            return self._serialize_user(user)
        doc = {
            "user_id": user_id,
            "name": "Research User",
            "email": None,
            "password_hash": None,
            "credits": credits if credits is not None else INITIAL_CREDITS,
            "plan_status": "free",
            "token_version": 0,
            "is_active": True,
            "created_at": self._now(),
            "updated_at": self._now(),
            "last_login_at": None,
        }
        inserted = self.users.insert_one(doc)
        user = self.users.find_one({"_id": inserted.inserted_id})
        return self._serialize_user(user)
