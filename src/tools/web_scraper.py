"""Web scraper tool with HTML cleanup, readability heuristics, and token bounding."""

import logging
import re
from typing import Any, Dict
import requests
from bs4 import BeautifulSoup

from src.tools.base import BaseTool
from src.cache import ToolCache
from src.config import config

logger = logging.getLogger("research_agent.tools.web_scraper")


class WebScraperTool(BaseTool):
    """Fetches and extracts clean, readable text from a URL with noise filtering."""

    def __init__(self, cache: ToolCache = None, max_chars: int = None):
        super().__init__(
            name="web_scraper",
            description="Fetches a webpage, strips HTML markup and ads, and extracts readable textual content.",
            cache=cache
        )
        self.max_chars = max_chars or config.scraper_max_chars

    def _run(self, url: str) -> Dict[str, Any]:
        # Validate URL schema
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 AIResearchAgent/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout_seconds)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.warning(f"HTTP request failed for {url}: {e}")
            raise RuntimeError(f"Failed to fetch URL ({url}): {e}")

        # Parse HTML and strip noisy elements
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove boilerplates, scripts, styles, navigation, footer, forms, ads
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"]):
            element.decompose()

        page_title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled Webpage"

        # Extract main text
        raw_text = soup.get_text(separator="\n")

        # Clean whitespace and empty lines
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)

        # Truncate to maximum characters
        is_truncated = len(cleaned_text) > self.max_chars
        bounded_text = cleaned_text[:self.max_chars]

        return {
            "title": page_title,
            "url": url,
            "content": bounded_text,
            "char_count": len(bounded_text),
            "is_truncated": is_truncated
        }
