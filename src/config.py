"""Configuration management for the AI Research Agent."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class AgentConfig(BaseModel):
    """Configuration settings for the agent execution."""

    # LLM Settings
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    openai_base_url: str = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", ""))

    # Operational Modes
    mock_mode: bool = Field(
        default_factory=lambda: os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")
    )

    # Tool Execution & Resilience
    search_max_results: int = Field(
        default_factory=lambda: int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    )
    tool_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("TOOL_TIMEOUT_SECONDS", "10.0"))
    )
    tool_max_retries: int = Field(
        default_factory=lambda: int(os.getenv("TOOL_MAX_RETRIES", "3"))
    )
    tool_retry_backoff_seconds: float = Field(
        default_factory=lambda: float(os.getenv("TOOL_RETRY_BACKOFF_SECONDS", "1.5"))
    )
    scraper_max_chars: int = Field(
        default_factory=lambda: int(os.getenv("SCRAPER_MAX_CHARS", "4000"))
    )

    # Caching
    enable_cache: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_CACHE", "true").lower() in ("true", "1", "yes")
    )
    cache_ttl_seconds: int = Field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "86400"))
    )
    cache_dir: Path = BASE_DIR / "data" / "cache"

    # Traces & Observability
    save_traces: bool = Field(
        default_factory=lambda: os.getenv("SAVE_TRACES", "true").lower() in ("true", "1", "yes")
    )
    traces_dir: Path = BASE_DIR / "traces"
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# Global default configuration instance
config = AgentConfig()
