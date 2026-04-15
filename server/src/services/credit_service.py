from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument

from src.core.config import INITIAL_CREDITS
from src.core.database import get_database, get_mongo_client


class CreditService:
    def __init__(self):
        self.db = None
        self.users = None
        self.transactions = None

    def _ensure_collections(self):
        if self.db is None:
            self.db = get_database()
            self.users = self.db.users
            self.transactions = self.db.credit_transactions

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _serialize_transaction(self, tx: dict[str, Any]) -> dict[str, Any]:
        tx["id"] = str(tx.pop("_id"))
        if isinstance(tx.get("user_id"), ObjectId):
            tx["user_id"] = str(tx["user_id"])
        if isinstance(tx.get("session_id"), ObjectId):
            tx["session_id"] = str(tx["session_id"])
        return tx

    def get_or_create_user(self, user_id: str) -> dict[str, Any]:
        self._ensure_collections()
        user = self.users.find_one({"user_id": user_id})
        if user:
            user["id"] = str(user.pop("_id"))
            return user

        result = self.users.insert_one(
            {
                "user_id": user_id,
                "credits": INITIAL_CREDITS,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
        )
        user = self.users.find_one({"_id": result.inserted_id})
        user["id"] = str(user.pop("_id"))
        return user

    def get_balance(self, user_id: str) -> int:
        self._ensure_collections()
        user = self.users.find_one({"user_id": user_id}, {"credits": 1})
        if not user:
            return INITIAL_CREDITS
        return int(user.get("credits", 0))

    def reserve_credits(
        self,
        user_id: str,
        amount: int,
        *,
        reason: str,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> tuple[int, str]:
        self._ensure_collections()
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        client = get_mongo_client()
        metadata = metadata or {}

        with client.start_session() as session:
            with session.start_transaction():
                user = self.users.find_one({"user_id": user_id}, session=session)
                if not user:
                    user = {
                        "user_id": user_id,
                        "credits": INITIAL_CREDITS,
                        "created_at": self._now(),
                        "updated_at": self._now(),
                    }
                    inserted = self.users.insert_one(user, session=session)
                    user = self.users.find_one({"_id": inserted.inserted_id}, session=session)

                current_credits = int(user.get("credits", 0))
                if current_credits < amount:
                    raise ValueError("Insufficient credits")

                updated = self.users.find_one_and_update(
                    {"user_id": user_id, "credits": {"$gte": amount}},
                    {
                        "$inc": {"credits": -amount},
                        "$set": {"updated_at": self._now()},
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )

                if not updated:
                    raise ValueError("Insufficient credits")

                tx = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": "debit",
                    "amount": amount,
                    "reason": reason,
                    "metadata": metadata,
                    "created_at": self._now(),
                }
                inserted_tx = self.transactions.insert_one(tx, session=session)

                return int(updated.get("credits", 0)), str(inserted_tx.inserted_id)

    def refund_credits(
        self,
        user_id: str,
        amount: int,
        *,
        reason: str,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> tuple[int, str]:
        self._ensure_collections()
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        client = get_mongo_client()
        metadata = metadata or {}

        with client.start_session() as session:
            with session.start_transaction():
                updated = self.users.find_one_and_update(
                    {"user_id": user_id},
                    {
                        "$inc": {"credits": amount},
                        "$set": {"updated_at": self._now()},
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )

                if not updated:
                    raise ValueError("User not found")

                tx = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": "credit",
                    "amount": amount,
                    "reason": reason,
                    "metadata": metadata,
                    "created_at": self._now(),
                }
                inserted_tx = self.transactions.insert_one(tx, session=session)

                return int(updated.get("credits", 0)), str(inserted_tx.inserted_id)

    def grant_credits(
        self,
        user_id: str,
        amount: int,
        *,
        reason: str,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> tuple[int, str]:
        self._ensure_collections()
        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        client = get_mongo_client()
        metadata = metadata or {}

        with client.start_session() as session:
            with session.start_transaction():
                updated = self.users.find_one_and_update(
                    {"user_id": user_id},
                    {
                        "$inc": {"credits": amount},
                        "$set": {"updated_at": self._now()},
                    },
                    return_document=ReturnDocument.AFTER,
                    session=session,
                )

                if not updated:
                    raise ValueError("User not found")

                tx = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "type": "credit",
                    "amount": amount,
                    "reason": reason,
                    "metadata": metadata,
                    "created_at": self._now(),
                }
                inserted_tx = self.transactions.insert_one(tx, session=session)

                return int(updated.get("credits", 0)), str(inserted_tx.inserted_id)

    def attach_session_to_transaction(self, transaction_id: str, session_id: str) -> None:
        self._ensure_collections()
        self.transactions.update_one(
            {"_id": ObjectId(transaction_id)},
            {"$set": {"session_id": session_id}},
        )

    def list_transactions_by_user(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        self._ensure_collections()
        transactions = list(
            self.transactions.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        )
        for transaction in transactions:
            transaction["id"] = str(transaction.pop("_id"))
        return transactions

    def list_transactions_by_session(self, session_id: str) -> list[dict[str, Any]]:
        self._ensure_collections()
        transactions = list(
            self.transactions.find({"session_id": session_id}).sort("created_at", -1)
        )
        for transaction in transactions:
            transaction["id"] = str(transaction.pop("_id"))
        return transactions
