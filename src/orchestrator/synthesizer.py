"""Final answer synthesis module producing strict, source-grounded ResearchReport outputs."""

import logging
from typing import List, Optional
from src.llm_client import LLMClient
from src.models import ConfidenceLevel, ResearchReport, SourceItem
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent.synthesizer")

SYNTHESIZER_SYSTEM_PROMPT = """You are a rigorous Principal Research Analyst.
Your mission is to synthesize a structured, definitive research report based STRICTLY on the provided external evidence sources.

Output Requirements:
1. 'user_question': The exact question asked by the user.
2. 'short_answer': A direct, punchy executive summary answering the question in 2-3 sentences.
3. 'key_findings': 3 to 5 detailed bullet points. Every single bullet point MUST cite its supporting sources using brackets like [1], [2].
4. 'sources_used': Complete list of sources referenced.
5. 'confidence_level': 'High', 'Medium', or 'Low'.
   - 'High': Multiple corroborating, authoritative sources directly address the question.
   - 'Medium': Plausible evidence gathered, but limited by small sample size or conflicting details.
   - 'Low': Sparse evidence, unverified sources, or largely extrapolated conclusions.
6. 'confidence_rationale': 1-2 sentences explaining why this confidence rating was assigned.
7. 'limitations_or_assumptions': Explicitly list unknown variables, potential biases, temporal boundaries, or operating assumptions.
8. 'suggested_next_steps': 2 to 3 actionable next steps for a practitioner or researcher to dive deeper.

Integrity Rules:
- DO NOT invent facts, metrics, or citations not present in the provided evidence.
- If evidence is missing or ambiguous, state that honestly in the limitations.
- Enforce bracketed citations [1], [2] in all key findings.
"""


class ResearchSynthesizer:
    """Synthesizes filtered research evidence into a validated ResearchReport."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def synthesize(
        self,
        query: str,
        sources: List[SourceItem],
        evidence_context: str,
        tracer: Optional[ResearchTracer] = None
    ) -> ResearchReport:
        """Generates the structured research report."""
        logger.info(f"Synthesizing final research report for: '{query}'")

        sources_summary = "\n".join([
            f"[{s.source_id}] {s.title} ({s.url}) - Domain: {s.domain}"
            for s in sources
        ]) or "No external sources available."

        user_prompt = (
            f"User Question: {query}\n\n"
            f"Available Sources:\n{sources_summary}\n\n"
            f"Gathered Evidence Text:\n{evidence_context}\n\n"
            "Synthesize the structured ResearchReport conforming to the required schema."
        )

        try:
            report = self.llm.generate_structured(
                schema=ResearchReport,
                system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                tracer=tracer,
                phase="synthesis"
            )

            # Ensure sources_used is populated with the verified sources
            if not report.sources_used and sources:
                report.sources_used = sources
            elif sources:
                # Merge or reconcile
                existing_urls = {s.url for s in report.sources_used}
                for s in sources:
                    if s.url not in existing_urls:
                        report.sources_used.append(s)

            # Ensure question matches
            report.user_question = query

            return report

        except Exception as e:
            logger.error(f"Synthesis failed with error: {e}. Generating graceful fallback report.")
            return self._build_fallback_report(query, sources)

    def _build_fallback_report(self, query: str, sources: List[SourceItem]) -> ResearchReport:
        """Fallback report ensuring valid schema delivery even during catastrophic LLM failures."""
        findings = [
            f"Information retrieved from {len(sources)} sources regarding '{query[:50]}'."
        ]
        for s in sources[:3]:
            findings.append(f"According to [{s.source_id}] {s.title}: {s.snippet[:120]}... [{s.source_id}]")

        return ResearchReport(
            user_question=query,
            short_answer=f"Investigation completed for: {query}. Evidence gathered across {len(sources)} reference sources.",
            key_findings=findings,
            sources_used=sources,
            confidence_level=ConfidenceLevel.MEDIUM if sources else ConfidenceLevel.LOW,
            confidence_rationale="Report constructed from direct evidence extractions due to LLM fallback handling.",
            limitations_or_assumptions=[
                "Automated fallback mode was engaged.",
                "Depth of qualitative synthesis may be reduced."
            ],
            suggested_next_steps=[
                "Review the listed raw reference URLs directly.",
                "Re-run the query with expanded search terms."
            ]
        )
