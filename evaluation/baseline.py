"""Non-agentic baseline: single-shot LLM completion without tools or planning."""

import time
from typing import Dict, Any
from src.llm_client import LLMClient
from src.config import config


class NonAgenticBaseline:
    """Represents a standard non-agentic LLM wrapper (direct one-shot prompt)."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def run(self, query: str) -> Dict[str, Any]:
        """Runs the query directly against the LLM without tools, search, or planning."""
        start_time = time.perf_counter()

        system_prompt = (
            "You are an AI assistant. Answer the user question based solely on your internal training knowledge. "
            "Do not perform external searches or tool calls."
        )

        resp = self.llm.generate(
            system_prompt=system_prompt,
            user_prompt=query,
            phase="baseline_run"
        )

        elapsed = time.perf_counter() - start_time

        return {
            "query": query,
            "response_text": resp.content,
            "latency_seconds": round(elapsed, 3),
            "tools_used": 0,
            "has_live_citations": False,
            "source_count": 0
        }
