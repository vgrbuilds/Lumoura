import os
from langchain_google_genai import ChatGoogleGenerativeAI


class GeminiService:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY missing")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=api_key
        )

    def generate(self, prompt: str):
        return self.llm.invoke(prompt).content


_gemini = None


def get_llm():
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini


def generate(prompt: str):
    return get_llm().generate(prompt)