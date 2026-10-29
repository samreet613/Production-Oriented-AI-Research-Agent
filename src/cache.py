"""TTL-based caching layer for tools and intermediate search results."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class ToolCache:
    """Provides fast in-memory and persistent disk caching for tool results."""

    def __init__(self, cache_dir: Path, ttl_seconds: int = 86400, enabled: bool = True):
        self.cache_dir = cache_dir
        self.ttl_seconds = ttl_seconds
        self.enabled = enabled
        self._memory_cache = {}

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash_key(self, tool_name: str, query: str) -> str:
        raw = f"{tool_name}::{query.strip().lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, tool_name: str, query: str) -> Optional[Any]:
        if not self.enabled:
            return None

        key = self._hash_key(tool_name, query)
        now = time.time()

        # 1. Check memory cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if now - entry["timestamp"] <= self.ttl_seconds:
                return entry["data"]
            else:
                del self._memory_cache[key]

        # 2. Check disk cache
        file_path = self.cache_dir / f"{key}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if now - entry.get("timestamp", 0) <= self.ttl_seconds:
                    self._memory_cache[key] = entry
                    return entry.get("data")
                else:
                    file_path.unlink(missing_ok=True)
            except Exception:
                pass

        return None

    def set(self, tool_name: str, query: str, data: Any):
        if not self.enabled:
            return

        key = self._hash_key(tool_name, query)
        entry = {
            "tool": tool_name,
            "query": query,
            "timestamp": time.time(),
            "data": data
        }
        self._memory_cache[key] = entry

        try:
            file_path = self.cache_dir / f"{key}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, default=str)
        except Exception:
            pass

    def clear(self):
        """Clear memory and disk cache."""
        self._memory_cache.clear()
        if self.cache_dir.exists():
            for f in self.cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)
