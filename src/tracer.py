"""Observability and execution tracing for the research agent."""

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("research_agent")


class TraceEvent:
    """Individual lifecycle event in the agent execution."""

    def __init__(
        self,
        event_type: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        status: str = "ok",
        error: Optional[str] = None
    ):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.phase = phase
        self.data = data or {}
        self.duration_ms = duration_ms
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "phase": self.phase,
            "duration_ms": round(self.duration_ms, 2),
            "status": self.status,
            "error": self.error,
            "data": self.data
        }


class ResearchTracer:
    """Tracks the end-to-end execution, lifecycle spans, tool calls, and metrics."""

    def __init__(self, query: str, trace_id: Optional[str] = None):
        self.trace_id = trace_id or f"trace_{uuid.uuid4().hex[:10]}"
        self.query = query
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.events: List[TraceEvent] = []
        self.tool_calls_count = 0
        self.failed_tool_calls_count = 0
        self.retries_count = 0
        self.cache_hits_count = 0
        self.total_tokens_estimated = 0

    def log_event(
        self,
        event_type: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        duration_ms: float = 0.0,
        status: str = "ok",
        error: Optional[str] = None
    ):
        """Append a structured trace event."""
        event = TraceEvent(event_type, phase, data, duration_ms, status, error)
        self.events.append(event)
        log_msg = f"[{phase}] {event_type} - status={status}"
        if duration_ms > 0:
            log_msg += f" ({duration_ms:.1f}ms)"
        if error:
            log_msg += f" | error: {error}"
            logger.warning(log_msg)
        else:
            logger.debug(log_msg)

    def record_tool_call(self, tool_name: str, query: str, success: bool, duration_ms: float, retries: int = 0, cached: bool = False, error: Optional[str] = None):
        self.tool_calls_count += 1
        self.retries_count += retries
        if cached:
            self.cache_hits_count += 1
        if not success:
            self.failed_tool_calls_count += 1

        self.log_event(
            event_type="tool_execution",
            phase="execution",
            data={
                "tool": tool_name,
                "target": query,
                "retries": retries,
                "cached": cached
            },
            duration_ms=duration_ms,
            status="success" if success else "failed",
            error=error
        )

    def record_llm_call(self, phase: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0, duration_ms: float = 0.0):
        total = prompt_tokens + completion_tokens
        self.total_tokens_estimated += total
        self.log_event(
            event_type="llm_inference",
            phase=phase,
            data={
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total
            },
            duration_ms=duration_ms,
            status="success"
        )

    def finish(self) -> float:
        """Mark completion and return elapsed wall clock time in seconds."""
        self.end_time = time.perf_counter()
        elapsed = self.end_time - self.start_time
        self.log_event(
            event_type="agent_finished",
            phase="orchestration",
            data={
                "total_duration_seconds": round(elapsed, 3),
                "total_tool_calls": self.tool_calls_count,
                "cache_hits": self.cache_hits_count,
                "failed_tools": self.failed_tool_calls_count,
                "retries": self.retries_count,
                "estimated_tokens": self.total_tokens_estimated
            },
            duration_ms=elapsed * 1000.0
        )
        return elapsed

    def export_summary(self) -> Dict[str, Any]:
        """Export trace metrics as a dictionary."""
        elapsed = (self.end_time or time.perf_counter()) - self.start_time
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "total_duration_seconds": round(elapsed, 3),
            "tool_calls_count": self.tool_calls_count,
            "failed_tool_calls_count": self.failed_tool_calls_count,
            "retries_count": self.retries_count,
            "cache_hits_count": self.cache_hits_count,
            "total_tokens_estimated": self.total_tokens_estimated,
            "event_count": len(self.events)
        }

    def save_to_file(self, target_dir: Path) -> Path:
        """Save the detailed trace events to a JSON file."""
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{self.trace_id}.json"
        payload = {
            "summary": self.export_summary(),
            "events": [e.to_dict() for e in self.events]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return file_path
