from src.services.gemini_service import generate
import json

def plan(query: str):
    prompt = f"""
Break this query into 2-3 short search queries.

Return ONLY a valid JSON list.
Example:
["query 1", "query 2"]

Query: {query}
"""
    result = generate(prompt)

    try:
        return json.loads(result)
    except:
        return [query]
    
