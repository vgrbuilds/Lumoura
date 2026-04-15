from src.services.research_service import ResearchService
from src.services.scraper_service import ScraperService
from src.services.synthesizer_service import SynthesizerService


class ResearchPipeline:

    def __init__(self):
        self.tavily = ResearchService()
        self.scraper = ScraperService()
        self.synthesizer = SynthesizerService()

    def run(self, query: str, preferences: dict | None = None):
        preferences = preferences or {}

        # 1. Search
        search_data = self.tavily.search(query)

        results = search_data.get("results", [])

        # 2. Select top URLs (keep it small)
        max_sources = int(preferences.get("max_sources") or 3)
        top_urls = results[:max_sources]

        scraped_sources = []

        # 3. Scrape each URL
        for r in top_urls:
            url = r.get("url")
            if not url:
                continue

            try:
                data = self.scraper.fetch(url)
                scraped_sources.append(
                    {
                        "title": r.get("title"),
                        "url": data.get("url", url),
                        "content": data.get("content"),
                        "snippet": r.get("content"),
                        "source_type": "scraped",
                    }
                )
            except Exception:
                continue

        # 4. If scraping fails, fallback to Tavily snippets
        if not scraped_sources:
            scraped_sources = [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content"),
                    "snippet": r.get("content"),
                    "source_type": "snippet",
                }
                for r in results[:3]
            ]

        # 5. Synthesize final answer
        final = self.synthesizer.synthesize(query, scraped_sources, preferences)

        return {
            "query": query,
            "answer": final["answer"],
            "sources": final["sources"],
            "sources_used": final["sources_used"],
            "search_results": results[:max_sources],
            "preferences": final["preferences"],
        }
    
