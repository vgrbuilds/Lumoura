from __future__ import annotations

from typing import Any

from src.services.cloudinary_service import CloudinaryService
from src.services.file_asset_service import FileAssetService


class ResearchExportService:
    def __init__(self):
        self.cloudinary = CloudinaryService()
        self.file_assets = FileAssetService()

    def build_markdown(
        self,
        *,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        preferences: dict[str, Any],
    ) -> str:
        source_blocks = []
        for i, src in enumerate(sources, start=1):
            source_blocks.append(
                f"""### Source {i}
- Title: {src.get("title") or "Untitled"}
- URL: {src.get("url") or "N/A"}
- Type: {src.get("source_type") or "snippet"}

{(src.get("content") or src.get("snippet") or "")[:1500]}
"""
            )

        preference_lines = "\n".join(
            f"- {key}: {value}"
            for key, value in preferences.items()
            if value not in (None, "", [], {})
        )

        return f"""# Lumoura Research Export

## Query
{query}

## Preferences
{preference_lines or "- none"}

## Answer
{answer}

## Sources
{chr(10).join(source_blocks) if source_blocks else "No sources available."}
"""

    def export(
        self,
        *,
        user_id: str,
        session_id: str | None,
        query: str,
        answer: str,
        sources: list[dict[str, Any]],
        preferences: dict[str, Any],
    ) -> dict[str, Any] | None:
        content = self.build_markdown(
            query=query,
            answer=answer,
            sources=sources,
            preferences=preferences,
        )
        filename = f"{session_id or 'research'}-export.md"
        public_id = f"{user_id}/{session_id or 'research-export'}"
        cloudinary_payload = self.cloudinary.upload_text(
            content=content,
            public_id=public_id,
            filename=filename,
        )
        asset = self.file_assets.create_asset(
            user_id=user_id,
            session_id=session_id,
            asset_type="research_export",
            filename=filename,
            cloudinary_payload=cloudinary_payload,
            metadata={
                "query": query,
                "preference_snapshot": preferences,
            },
        )
        return asset
