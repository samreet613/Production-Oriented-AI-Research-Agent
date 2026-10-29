"""Unit tests for tool resilience, caching, and error isolation."""

import pytest
from src.tools.web_search import WebSearchTool
from src.tools.web_scraper import WebScraperTool
from src.tools.academic_search import AcademicSearchTool
from src.cache import ToolCache
from src.config import AgentConfig


def test_empty_input_handling():
    """Ensure tools reject empty inputs gracefully without throwing uncaught exceptions."""
    tool = WebSearchTool()
    output = tool.execute("   ")
    assert not output.success
    assert "cannot be empty" in output.error.lower()


def test_web_search_fallback():
    """Verify web search returns valid structured results."""
    tool = WebSearchTool()
    output = tool.execute("vector databases")
    assert output.success
    assert isinstance(output.data, list)
    assert len(output.data) > 0
    assert "title" in output.data[0]
    assert "url" in output.data[0]


def test_tool_cache(tmp_path):
    """Verify tool cache eliminates duplicate external requests."""
    cache = ToolCache(cache_dir=tmp_path, ttl_seconds=60, enabled=True)
    tool = WebSearchTool(cache=cache)

    # First call - cache miss
    out1 = tool.execute("vector search")
    assert not out1.from_cache

    # Second call - cache hit
    out2 = tool.execute("vector search")
    assert out2.from_cache
    assert out2.data == out1.data


def test_web_scraper_invalid_url():
    """Ensure scraper handles non-existent or malformed domains gracefully."""
    scraper = WebScraperTool(max_chars=500)
    output = scraper.execute("https://invalid-non-existent-domain-99999.xyz")
    assert not output.success
    assert output.error is not None
