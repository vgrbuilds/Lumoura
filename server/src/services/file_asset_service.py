from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId

from src.core.database import get_database


class FileAssetService:
    def __init__(self):
        self.db = None
        self.assets = None
        self._ready = False

    def _ensure_collection(self):
        if self.db is None:
            self.db = get_database()
            self.assets = self.db.file_assets
        if not self._ready:
            self.assets.create_index("user_id")
            self.assets.create_index("session_id", unique=True, sparse=True)
            self.assets.create_index("cloudinary_public_id", unique=True, sparse=True)
            self._ready = True

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_asset(
        self,
        *,
        user_id: str,
        session_id: str | None,
        asset_type: str,
        filename: str,
        cloudinary_payload: dict[str, Any] | None,
        content_type: str = "text/markdown",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._ensure_collection()
        metadata = metadata or {}
        doc = {
            "user_id": user_id,
            "asset_type": asset_type,
            "filename": filename,
            "content_type": content_type,
            "metadata": metadata,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        if session_id is not None:
            doc["session_id"] = session_id
        if cloudinary_payload:
            doc["cloudinary_public_id"] = cloudinary_payload.get("public_id")
            doc["cloudinary_url"] = cloudinary_payload.get("secure_url")
            doc["cloudinary_resource_type"] = cloudinary_payload.get("resource_type")
            doc["cloudinary_format"] = cloudinary_payload.get("format")
            doc["bytes"] = int(cloudinary_payload.get("bytes", 0))
        inserted = self.assets.insert_one(doc)
        created = self.assets.find_one({"_id": inserted.inserted_id})
        created["id"] = str(created.pop("_id"))
        return created

    def get_asset(self, asset_id: str) -> dict[str, Any] | None:
        self._ensure_collection()
        asset = self.assets.find_one({"_id": ObjectId(asset_id)})
        if not asset:
            return None
        asset["id"] = str(asset.pop("_id"))
        return asset

    def get_asset_by_session(self, session_id: str) -> dict[str, Any] | None:
        self._ensure_collection()
        asset = self.assets.find_one({"session_id": session_id})
        if not asset:
            return None
        asset["id"] = str(asset.pop("_id"))
        return asset

    def list_assets_by_user(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        self._ensure_collection()
        assets = list(self.assets.find({"user_id": user_id}).sort("created_at", -1).limit(limit))
        for asset in assets:
            asset["id"] = str(asset.pop("_id"))
        return assets
