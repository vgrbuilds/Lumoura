from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any

import requests

from src.core.config import (
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_FOLDER,
)


class CloudinaryService:
    def __init__(self):
        self.base_url = (
            f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/raw/upload"
            if CLOUDINARY_CLOUD_NAME
            else None
        )

    def is_enabled(self) -> bool:
        return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _signature(self, params: dict[str, Any]) -> str:
        to_sign = "&".join(
            f"{key}={params[key]}"
            for key in sorted(params)
            if params.get(key) not in (None, "")
        )
        digest = hmac.new(
            CLOUDINARY_API_SECRET.encode("utf-8"),
            to_sign.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest()
        return digest

    def upload_text(
        self,
        *,
        content: str,
        public_id: str,
        filename: str,
        folder: str | None = None,
    ) -> dict[str, Any] | None:
        if not self.is_enabled():
            return None

        folder = folder or CLOUDINARY_FOLDER
        timestamp = self._now()
        params = {
            "timestamp": timestamp,
            "public_id": public_id,
            "folder": folder,
        }
        signature = self._signature({k: str(v) for k, v in params.items()})
        files = {
            "file": (filename, content.encode("utf-8"), "text/markdown"),
        }
        data = {
            "api_key": CLOUDINARY_API_KEY,
            "timestamp": timestamp,
            "signature": signature,
            "public_id": public_id,
            "folder": folder,
            "resource_type": "raw",
            "filename_override": filename,
        }
        response = requests.post(self.base_url, data=data, files=files, timeout=30)
        response.raise_for_status()
        return response.json()
