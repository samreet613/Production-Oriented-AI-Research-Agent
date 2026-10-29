"""Unit tests for Pydantic schema validation and model constraints."""

import pytest
from pydantic import ValidationError
from src.models import (
    ConfidenceLevel,
    PlanStep,
    ResearchPlan,
    ResearchReport,
    SourceItem,
    ToolType
)


def test_research_report_valid_schema():
    """Verify ResearchReport initializes properly with all required fields."""
    source = SourceItem(
        source_id=1,
        title="Qdrant Docs",
        url="https://qdrant.tech",
        snippet="High-performance vector search engine.",
        domain="qdrant.tech"
    )
    report = ResearchReport(
        user_question="Compare vector databases",
        short_answer="Qdrant and Chroma are top choices.",
        key_findings=["Qdrant is written in Rust [1]."],
        sources_used=[source],
        confidence_level=ConfidenceLevel.HIGH,
        confidence_rationale="Well supported by documentation.",
        limitations_or_assumptions=["Evaluated for early stage RAG."],
        suggested_next_steps=["Run synthetic benchmarks."]
    )
    assert report.confidence_level == ConfidenceLevel.HIGH
    assert len(report.sources_used) == 1
    assert report.sources_used[0].source_id == 1


def test_plan_step_tool_validation():
    """Verify PlanStep rejects invalid tool names."""
    with pytest.raises(ValidationError):
        PlanStep(
            step_id=1,
            objective="Do research",
            tool="unregistered_tool_xyz",  # Invalid enum value
            query_or_target="something",
            rationale="why"
        )
