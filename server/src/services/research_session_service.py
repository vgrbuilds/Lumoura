from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from src.core.database import get_database


class ResearchSessionService:
    def __init__(self):
        self.db = None
        self.sessions = None

    def _ensure_collection(self):
        if self.db is None:
            self.db = get_database()
            self.sessions = self.db.research_sessions

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_pending_session(
        self,
        *,
        user_id: str,
        query: str,
        preferences: dict[str, Any],
        credits_cost: int,
        debit_transaction_id: str | None,
    ) -> str:
        self._ensure_collection()
        result = self.sessions.insert_one(
            {
                "user_id": user_id,
                "query": query,
                "answer": None,
                "sources": [],
                "search_results": [],
                "preferences": preferences,
                "status": "pending",
                "credits_cost": credits_cost,
                "debit_transaction_id": debit_transaction_id,
                "refund_transaction_id": None,
                "export": None,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
        )
        return str(result.inserted_id)

    def complete_session(
        self,
        session_id: str,
        *,
        answer: str,
        sources: list[dict[str, Any]],
        search_results: list[dict[str, Any]],
        preferences: dict[str, Any],
        export: dict[str, Any] | None = None,
    ) -> None:
        self._ensure_collection()
        self.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "answer": answer,
                    "sources": sources,
                    "search_results": search_results,
                    "preferences": preferences,
                    "export": export,
                    "status": "complete",
                    "updated_at": self._now(),
                }
            },
        )

    def fail_session(self, session_id: str, error_message: str) -> None:
        self._ensure_collection()
        self.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "status": "failed",
                    "error": error_message,
                    "updated_at": self._now(),
                }
            },
        )

    def attach_refund_transaction(self, session_id: str, refund_transaction_id: str) -> None:
        self._ensure_collection()
        self.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "refund_transaction_id": refund_transaction_id,
                    "updated_at": self._now(),
                }
            },
        )

    def attach_debit_transaction(self, session_id: str, debit_transaction_id: str) -> None:
        self._ensure_collection()
        self.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "debit_transaction_id": debit_transaction_id,
                    "updated_at": self._now(),
                }
            },
        )

    def attach_export(self, session_id: str, export: dict[str, Any]) -> None:
        self._ensure_collection()
        self.sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "export": export,
                    "updated_at": self._now(),
                }
            },
        )

    def list_sessions_by_user(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        self._ensure_collection()
        sessions = list(
            self.sessions.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        )
        for session in sessions:
            session["id"] = str(session.pop("_id"))
        return sessions

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        self._ensure_collection()
        session = self.sessions.find_one({"_id": ObjectId(session_id)})
        if not session:
            return None
        session["id"] = str(session.pop("_id"))
        return session
