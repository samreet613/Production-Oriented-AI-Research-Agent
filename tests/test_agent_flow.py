"""Integration test for full ResearchAgent workflow."""

from src.agent import ResearchAgent
from src.config import AgentConfig
from src.models import ConfidenceLevel, ResearchReport


def test_agent_end_to_end_mock():
    """Verify end-to-end execution completes and returns valid structured models."""
    cfg = AgentConfig(mock_mode=True)
    agent = ResearchAgent(cfg=cfg)

    query = "Compare the top 3 open-source vector databases for a startup building RAG products."
    report, plan, judge_eval, tracer = agent.run(query)

    # 1. Plan Verification
    assert len(plan.steps) >= 2
    assert plan.original_query == query

    # 2. Output Schema Verification
    assert isinstance(report, ResearchReport)
    assert report.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW)
    assert len(report.key_findings) > 0
    assert len(report.sources_used) > 0

    # 3. Grounding Verification
    assert judge_eval.grounding_score >= 0.7
    assert judge_eval.verdict in ("Pass", "Caution")

    # 4. Observability & Tracing
    assert tracer.tool_calls_count >= 1
    assert tracer.finish() > 0
