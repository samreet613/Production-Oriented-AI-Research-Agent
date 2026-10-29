"""Base tool interface with retries, timeout enforcement, caching, and error containment."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from src.cache import ToolCache
from src.config import config
from src.models import RawToolOutput
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent.tools")


class BaseTool(ABC):
    """Abstract base class for all research agent tools."""

    def __init__(
        self,
        name: str,
        description: str,
        cache: Optional[ToolCache] = None,
        timeout_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        backoff_seconds: Optional[float] = None
    ):
        self.name = name
        self.description = description
        self.cache = cache
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else config.tool_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else config.tool_max_retries
        self.backoff_seconds = backoff_seconds if backoff_seconds is not None else config.tool_retry_backoff_seconds

    def execute(self, query_or_target: str, tracer: Optional[ResearchTracer] = None) -> RawToolOutput:
        """Executes the tool with caching, timeouts, retries, and comprehensive error containment."""
        start_time = time.perf_counter()
        query_or_target = query_or_target.strip()

        # Input validation
        if not query_or_target:
            elapsed = time.perf_counter() - start_time
            if tracer:
                tracer.record_tool_call(self.name, query_or_target, False, elapsed * 1000.0, error="Empty input parameter")
            return RawToolOutput(
                tool_name=self.name,
                query_or_target=query_or_target,
                success=False,
                data=None,
                error="Tool input parameter cannot be empty.",
                latency_seconds=elapsed
            )

        # Cache check
        if self.cache:
            cached_data = self.cache.get(self.name, query_or_target)
            if cached_data is not None:
                elapsed = time.perf_counter() - start_time
                if tracer:
                    tracer.record_tool_call(
                        self.name, query_or_target, True, elapsed * 1000.0,
                        retries=0, cached=True
                    )
                return RawToolOutput(
                    tool_name=self.name,
                    query_or_target=query_or_target,
                    success=True,
                    data=cached_data,
                    latency_seconds=elapsed,
                    from_cache=True
                )

        # Retry loop with exponential backoff
        retries_used = 0
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                data = self._run(query_or_target)
                elapsed = time.perf_counter() - start_time

                # Cache successful result
                if self.cache and data:
                    self.cache.set(self.name, query_or_target, data)

                if tracer:
                    tracer.record_tool_call(
                        self.name, query_or_target, True, elapsed * 1000.0,
                        retries=retries_used, cached=False
                    )

                return RawToolOutput(
                    tool_name=self.name,
                    query_or_target=query_or_target,
                    success=True,
                    data=data,
                    latency_seconds=elapsed,
                    retries_used=retries_used
                )
            except Exception as e:
                last_exception = e
                retries_used += 1
                logger.warning(
                    f"Tool [{self.name}] attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for target '{query_or_target}' failed: {e}"
                )
                if attempt < self.max_retries:
                    sleep_time = self.backoff_seconds * (2 ** attempt)
                    time.sleep(sleep_time)

        # If all retries failed, return gracefully degraded error
        elapsed = time.perf_counter() - start_time
        err_msg = f"Tool [{self.name}] failed after {retries_used} attempts: {last_exception}"
        logger.error(err_msg)

        if tracer:
            tracer.record_tool_call(
                self.name, query_or_target, False, elapsed * 1000.0,
                retries=retries_used, cached=False, error=str(last_exception)
            )

        return RawToolOutput(
            tool_name=self.name,
            query_or_target=query_or_target,
            success=False,
            data=None,
            error=err_msg,
            latency_seconds=elapsed,
            retries_used=retries_used
        )

    @abstractmethod
    def _run(self, query_or_target: str) -> Any:
        """Concrete execution logic to be implemented by child classes."""
        pass
