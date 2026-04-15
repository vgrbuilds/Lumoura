from typing import Any

from tavily import TavilyClient

from src.core.config import TAVILY_API_KEY

class ResearchService:
    def __init__(self):
        self.api_key = TAVILY_API_KEY
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None

    def search(self, query: str) -> dict[str, Any]:
        if not self.client:
            return {"query": query, "results": []}

        response = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )

        return {
            "query": query,
            "answer": response.get("answer"),
            "results": [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content")
                }
                for r in response.get("results", [])
            ]
        }

    def run_research(self, query: str):
        from src.services.pipeline_service import ResearchPipeline

        return ResearchPipeline().run(query)
