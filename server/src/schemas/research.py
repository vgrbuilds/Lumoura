from typing import Any, Literal

from pydantic import BaseModel, Field


class ResearchPreferences(BaseModel):
    tone: str | None = Field(default=None, description="Desired writing tone")
    creativity: int | None = Field(default=None, ge=0, le=10, description="Creativity level from 0 to 10")
    audience: str | None = Field(default=None, description="Target audience for the answer")
    depth: Literal["brief", "balanced", "deep"] = "balanced"
    output_format: Literal["summary", "bullet_points", "report", "table"] = "report"
    language: str | None = Field(default=None, description="Preferred answer language")
    max_sources: int = Field(default=3, ge=1, le=10)
    extra_context: str | None = Field(default=None, description="Additional context to guide the research")
    include_citations: bool = True


class ResearchRequest(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, description="Unique user identifier")
    query: str = Field(..., min_length=2, description="User research query")
    preferences: ResearchPreferences = Field(default_factory=ResearchPreferences)


class ResearchSource(BaseModel):
    title: str | None = None
    url: str | None = None
    content: str | None = None
    snippet: str | None = None
    source_type: str | None = None


class ResearchExport(BaseModel):
    id: str | None = None
    cloudinary_public_id: str | None = None
    cloudinary_url: str | None = None
    cloudinary_resource_type: str | None = None
    cloudinary_format: str | None = None
    filename: str | None = None
    bytes: int | None = None


class ResearchResponse(BaseModel):
    session_id: str | None = None
    transaction_id: str | None = None
    export: ResearchExport | None = None
    user_id: str
    query: str
    answer: str
    sources_used: int
    credits_remaining: int | None = None
    preferences: ResearchPreferences = Field(default_factory=ResearchPreferences)
    sources: list[ResearchSource]
    search_results: list[dict[str, Any]] = Field(default_factory=list)


class UserCreditsResponse(BaseModel):
    user_id: str
    credits: int


class ResearchSessionSummary(BaseModel):
    id: str
    user_id: str
    query: str
    answer: str
    credits_cost: int
    status: str
    preferences: ResearchPreferences = Field(default_factory=ResearchPreferences)
    export: ResearchExport | None = None
