"""Registry for discovering, configuring, and invoking tools."""

from typing import Dict, List, Optional
from src.tools.base import BaseTool
from src.tools.web_search import WebSearchTool
from src.tools.web_scraper import WebScraperTool
from src.tools.academic_search import AcademicSearchTool
from src.cache import ToolCache
from src.config import config


class ToolRegistry:
    """Central registry and dispatcher for all research tools."""

    def __init__(self, cache: Optional[ToolCache] = None):
        self.cache = cache or ToolCache(
            cache_dir=config.cache_dir,
            ttl_seconds=config.cache_ttl_seconds,
            enabled=config.enable_cache
        )
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self.register(WebSearchTool(cache=self.cache))
        self.register(WebScraperTool(cache=self.cache))
        self.register(AcademicSearchTool(cache=self.cache))

    def register(self, tool: BaseTool):
        """Registers a tool instance."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieves a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """Returns metadata for all available tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    def has_tool(self, name: str) -> bool:
        return name in self._tools


# Global default registry instance
default_registry = ToolRegistry()
