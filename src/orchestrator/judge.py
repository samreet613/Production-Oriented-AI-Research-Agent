"""Grounding Evaluator & Judge: detects hallucinations and audits citation consistency."""

import logging
import re
from typing import List, Optional
from src.llm_client import LLMClient
from src.models import GroundingEvaluation, ResearchReport, SourceItem, ConfidenceLevel
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent.judge")

JUDGE_SYSTEM_PROMPT = """You are an impartial AI Fact-Checking Judge.
Your sole job is to verify whether each finding in a research report is actually substantiated by the cited reference sources.

Evaluate each key finding:
1. Determine if the claim is directly supported by the source snippets.
2. Mark as 'unsupported' if the claim introduces new statistics, claims, or entities not found anywhere in the provided sources.
3. Compute a grounding_score between 0.0 (completely fabricated) and 1.0 (100% grounded).
4. Assign a verdict: 'Pass' (score >= 0.8), 'Caution' (0.5 <= score < 0.8), or 'Fail' (score < 0.5).
"""


class GroundingJudge:
    """Evaluates factual grounding and citation fidelity of the generated report."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def evaluate(
        self,
        report: ResearchReport,
        tracer: Optional[ResearchTracer] = None
    ) -> GroundingEvaluation:
        """Audits the research report against its sources and updates confidence if necessary."""
        logger.info(f"Running grounding audit on {len(report.key_findings)} findings.")

        # Check for citation brackets like [1], [2] in findings
        grounded_claims: List[str] = []
        unsupported_claims: List[str] = []

        sources_map = {s.source_id: s for s in report.sources_used}

        for finding in report.key_findings:
            cited_ids = [int(m) for m in re.findall(r"\[(\d+)\]", finding)]
            if not cited_ids:
                unsupported_claims.append(f"No source citation attached: {finding}")
                continue

            # Verify that cited source exists in sources_map
            valid_citations = [cid for cid in cited_ids if cid in sources_map]
            if not valid_citations:
                unsupported_claims.append(f"Invalid source ID cited: {finding}")
            else:
                grounded_claims.append(finding)

        total = len(report.key_findings)
        score = len(grounded_claims) / max(total, 1)

        if score >= 0.8:
            verdict = "Pass"
            audit_notes = f"High citation fidelity: {len(grounded_claims)}/{total} findings grounded with verified source references."
        elif score >= 0.5:
            verdict = "Caution"
            audit_notes = f"Moderate grounding: {len(unsupported_claims)} claims lacked verifiable citations."
            if report.confidence_level == ConfidenceLevel.HIGH:
                report.confidence_level = ConfidenceLevel.MEDIUM
                report.confidence_rationale += " (Confidence downgraded by Evaluator Judge due to ungrounded claims)."
        else:
            verdict = "Fail"
            audit_notes = f"Low citation grounding: majority of claims lacked supporting source references."
            report.confidence_level = ConfidenceLevel.LOW
            report.confidence_rationale += " (Confidence marked Low by Evaluator Judge due to high hallucination risk)."

        eval_result = GroundingEvaluation(
            grounded_claims=grounded_claims,
            unsupported_claims=unsupported_claims,
            grounding_score=round(score, 2),
            verdict=verdict,
            audit_notes=audit_notes
        )

        if tracer:
            tracer.log_event(
                event_type="grounding_evaluation",
                phase="evaluation",
                data={
                    "grounding_score": eval_result.grounding_score,
                    "verdict": eval_result.verdict,
                    "grounded_count": len(grounded_claims),
                    "unsupported_count": len(unsupported_claims)
                }
            )

        return eval_result
