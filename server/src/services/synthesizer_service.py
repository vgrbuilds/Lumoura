from src.services.gemini_service import generate

class SynthesizerService:

    def __init__(self):
        pass

    def build_prompt(self, query: str, sources: list, preferences: dict | None = None) -> str:
        preferences = preferences or {}

        context_blocks = []

        for i, src in enumerate(sources):
            context_blocks.append(
                f"""
SOURCE {i+1}
TITLE: {src.get('title') or 'Untitled'}
URL: {src.get('url')}
CONTENT:
{(src.get('content') or '')[:2000]}
"""
            )

        context = "\n\n".join(context_blocks)

        tone = preferences.get("tone") or "professional"
        creativity = preferences.get("creativity")
        audience = preferences.get("audience") or "general readers"
        depth = preferences.get("depth") or "balanced"
        output_format = preferences.get("output_format") or "report"
        language = preferences.get("language") or "English"
        extra_context = preferences.get("extra_context") or "None provided"
        include_citations = preferences.get("include_citations", True)
        citation_rule = "Include citations tied to source numbers." if include_citations else "Do not include explicit citations."

        prompt = f"""
You are a research assistant.

Task:
Answer the user query using ONLY the provided sources.

Rules:
- Do not hallucinate
- If info is missing, say "not found in sources"
- Keep answer structured and clear
- Add bullet points where needed
- Mention source number when used (e.g., Source 1)
- Write in {language}
- Target audience: {audience}
- Tone: {tone}
- Depth: {depth}
- Output format: {output_format}
- Creativity level: {creativity if creativity is not None else "default"}
- {citation_rule}

Query:
{query}

Extra context:
{extra_context}

Sources:
{context}

Return:
- Direct answer
- Key points
- Source mapping
"""

        return prompt

    def synthesize(self, query: str, sources: list, preferences: dict | None = None):

        prompt = self.build_prompt(query, sources, preferences)
        result = generate(prompt)

        return {
            "query": query,
            "answer": result,
            "sources_used": len(sources),
            "sources": sources,
            "preferences": preferences or {}
        }
