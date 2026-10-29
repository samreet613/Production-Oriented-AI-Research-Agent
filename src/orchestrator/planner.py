"""Planning module: decomposes research questions into focused, actionable steps."""

import logging
from typing import Optional
from src.llm_client import LLMClient
from src.models import ResearchPlan, PlanStep, ToolType
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent.planner")

PLANNER_SYSTEM_PROMPT = """You are an expert AI Research Architect.
Your task is to decompose a complex, research-oriented user inquiry into a structured, step-by-step investigation plan.

Available Tools:
- web_search: Best for searching recent industry news, benchmarks, competitor data, and technical documentation.
- web_scraper: Best for fetching and reading in-depth articles, product pages, or documentation from a known URL.
- academic_search: Best for retrieving scholarly research papers, formal algorithm evaluations, and peer-reviewed surveys from ArXiv.

Planning Rules:
1. Deconstruct the inquiry into 2 to 3 targeted, non-redundant steps.
2. Formulate specific, high-signal search queries (avoid overly generic keywords).
3. Choose the appropriate tool for each step based on the information type needed.
4. Provide a clear rationale explaining how this step addresses the research question.
5. Keep the plan lean: prioritize high-value discovery over exhaustive multi-hop crawls.
"""


class ResearchPlanner:
    """Creates a transparent, structured execution plan before invoking tools."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def create_plan(self, query: str, tracer: Optional[ResearchTracer] = None) -> ResearchPlan:
        """Generates a structured ResearchPlan for the user question."""
        logger.info(f"Generating research plan for query: '{query}'")

        user_prompt = f"Decompose this research inquiry into an execution plan:\n\nInquiry: {query}"

        try:
            plan = self.llm.generate_structured(
                schema=ResearchPlan,
                system_prompt=PLANNER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                tracer=tracer,
                phase="planning"
            )
            # Ensure at least 1 step is present
            if not plan.steps:
                raise ValueError("Plan contains zero execution steps.")
            plan.original_query = query
            return plan

        except Exception as e:
            logger.warning(f"Structured plan generation encountered an error: {e}. Building deterministic fallback plan.")
            return self._create_fallback_plan(query)

    def _create_fallback_plan(self, query: str) -> ResearchPlan:
        """Deterministic fallback planner when LLM is unavailable or fails schema validation."""
        lower_q = query.lower()

        # Decide whether academic search is relevant
        is_academic = any(term in lower_q for term in ["architecture", "paper", "algorithm", "benchmark", "theory"])

        steps = [
            PlanStep(
                step_id=1,
                objective="Collect foundational overviews, key players, and core concepts",
                tool=ToolType.WEB_SEARCH,
                query_or_target=f"{query} overview benchmark",
                rationale="Retrieve recent high-level documentation and industry consensus."
            ),
            PlanStep(
                step_id=2,
                objective="Investigate technical trade-offs, architecture patterns, and limitations",
                tool=ToolType.ACADEMIC_SEARCH if is_academic else ToolType.WEB_SEARCH,
                query_or_target=f"{query} architecture tradeoffs evaluation",
                rationale="Extract concrete pros, cons, and performance constraints."
            )
        ]

        return ResearchPlan(
            original_query=query,
            intent_analysis=f"Decomposed investigation for research topic: {query}",
            steps=steps,
            estimated_complexity="Medium"
        )
