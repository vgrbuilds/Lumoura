import requests
from bs4 import BeautifulSoup


class ScraperService:

    def __init__(self, timeout: int = 10, max_chars: int = 8000):
        self.timeout = timeout
        self.max_chars = max_chars

    def fetch_html(self, url: str) -> str:
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=self.timeout)
        res.raise_for_status()

        return res.text

    def clean_html(self, html: str) -> BeautifulSoup:
        soup = BeautifulSoup(html, "lxml")

        # remove noise
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        return soup

    def extract_text(self, soup: BeautifulSoup) -> str:
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split())  # normalize whitespace
        return text[:self.max_chars]

    def fetch(self, url: str) -> dict:
        html = self.fetch_html(url)
        soup = self.clean_html(html)
        text = self.extract_text(soup)

        return {
            "url": url,
            "content": text
        }
