"""Main ResearchAgent class: coordinates the end-to-end research lifecycle."""

import logging
from typing import Dict, Any, Optional, Tuple

from src.config import config, AgentConfig
from src.guardrails import SecurityGuardrails, GuardrailViolation
from src.llm_client import LLMClient
from src.models import (
    ConfidenceLevel,
    GroundingEvaluation,
    ResearchPlan,
    ResearchReport,
    SourceItem
)
from src.orchestrator.executor import PlanExecutor
from src.orchestrator.filter import EvidenceFilter
from src.orchestrator.judge import GroundingJudge
from src.orchestrator.planner import ResearchPlanner
from src.orchestrator.synthesizer import ResearchSynthesizer
from src.tools.registry import ToolRegistry, default_registry
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent")


class ResearchAgent:
    """Production-grade AI Research Agent implementing an inspectable, resilient pipeline."""

    def __init__(
        self,
        cfg: Optional[AgentConfig] = None,
        registry: Optional[ToolRegistry] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.cfg = cfg or config
        self.registry = registry or default_registry
        self.llm = llm_client or LLMClient(cfg=self.cfg)

        # Pipeline components
        self.planner = ResearchPlanner(self.llm)
        self.executor = PlanExecutor(self.registry)
        self.filter = EvidenceFilter()
        self.synthesizer = ResearchSynthesizer(self.llm)
        self.judge = GroundingJudge(self.llm)

    def run(
        self,
        query: str,
        on_step_callback: Optional[Any] = None
    ) -> Tuple[ResearchReport, ResearchPlan, GroundingEvaluation, ResearchTracer]:
        """
        Executes the full research workflow:
        1. Query Sanitization & Prompt Injection Guard
        2. Plan Generation
        3. Tool Execution & Data Gathering
        4. Information Filtering & Source Indexing
        5. Report Synthesis
        6. Grounding Evaluation & Confidence Calibration
        7. Tracing & Persistence
        """
        tracer = ResearchTracer(query=query)
        logger.info(f"Starting research run for: '{query}' [Trace ID: {tracer.trace_id}]")

        # 1. Guardrail Inspection
        sanitized_query = SecurityGuardrails.sanitize_input(query)
        violation: GuardrailViolation = SecurityGuardrails.inspect_query(sanitized_query)

        if not violation.is_safe:
            logger.warning(f"Guardrail triggered: {violation.reason}")
            tracer.log_event(
                event_type="guardrail_blocked",
                phase="guardrail",
                data={"reason": violation.reason, "risk": violation.risk_level},
                status="blocked"
            )
            elapsed = tracer.finish()

            blocked_report = ResearchReport(
                user_question=query,
                short_answer="The request could not be processed due to security policy enforcement.",
                key_findings=[
                    f"Safety Violation: {violation.reason} (Risk Level: {violation.risk_level}).",
                    "The system actively screens for prompt injections, system override directives, and invalid payload formats."
                ],
                sources_used=[],
                confidence_level=ConfidenceLevel.LOW,
                confidence_rationale="Rejected by input security guardrails.",
                limitations_or_assumptions=["Input violated security constraints."],
                suggested_next_steps=["Rephrase the research query without prompt-override keywords or administrative commands."],
                metadata={"status": "security_violation", "latency_seconds": round(elapsed, 3)}
            )
            empty_plan = ResearchPlan(
                original_query=query,
                intent_analysis="Execution blocked by security guardrails.",
                steps=[],
                estimated_complexity="N/A"
            )
            empty_judge = GroundingEvaluation(
                grounding_score=0.0,
                verdict="Fail",
                audit_notes="Blocked before execution."
            )
            return blocked_report, empty_plan, empty_judge, tracer

        # 2. Plan Generation
        tracer.log_event("planning_started", "planning")
        if on_step_callback:
            on_step_callback("planning", "Generating execution plan...")

        plan = self.planner.create_plan(sanitized_query, tracer=tracer)
        tracer.log_event(
            "planning_completed", "planning",
            data={"steps_count": len(plan.steps), "complexity": plan.estimated_complexity}
        )

        # 3. Tool Execution
        if on_step_callback:
            on_step_callback("execution", f"Executing {len(plan.steps)} planned tool steps...")

        plan, raw_outputs = self.executor.execute_plan(plan, tracer=tracer)

        # 4. Information Filtering
        tracer.log_event("filtering_started", "filtering")
        if on_step_callback:
            on_step_callback("filtering", "Filtering noisy content and deduplicating sources...")

        sources, evidence_context = self.filter.filter_and_index_sources(
            raw_outputs=raw_outputs,
            original_query=sanitized_query
        )
        tracer.log_event(
            "filtering_completed", "filtering",
            data={"sources_count": len(sources)}
        )

        # 5. Report Synthesis
        tracer.log_event("synthesis_started", "synthesis")
        if on_step_callback:
            on_step_callback("synthesis", "Synthesizing source-grounded report...")

        report = self.synthesizer.synthesize(
            query=sanitized_query,
            sources=sources,
            evidence_context=evidence_context,
            tracer=tracer
        )

        # 6. Evaluator / Grounding Judge
        tracer.log_event("grounding_evaluation_started", "evaluation")
        if on_step_callback:
            on_step_callback("evaluation", "Auditing citations and factual grounding...")

        judge_eval = self.judge.evaluate(report, tracer=tracer)

        # 7. Finalize Tracing & Metadata
        elapsed = tracer.finish()

        # Sanitize output against accidental credential leakage
        report.short_answer, _ = SecurityGuardrails.filter_malicious_output(report.short_answer)
        report.key_findings = [SecurityGuardrails.filter_malicious_output(f)[0] for f in report.key_findings]

        report.metadata = {
            "trace_id": tracer.trace_id,
            "latency_seconds": round(elapsed, 3),
            "tool_calls_count": tracer.tool_calls_count,
            "cache_hits_count": tracer.cache_hits_count,
            "failed_tools_count": tracer.failed_tool_calls_count,
            "grounding_score": judge_eval.grounding_score,
            "grounding_verdict": judge_eval.verdict,
            "estimated_tokens": tracer.total_tokens_estimated,
            "plan_steps_count": len(plan.steps)
        }

        # Save trace to disk if enabled
        if self.cfg.save_traces:
            try:
                saved_path = tracer.save_to_file(self.cfg.traces_dir)
                report.metadata["trace_file"] = str(saved_path)
            except Exception as e:
                logger.warning(f"Could not write trace to disk: {e}")

        logger.info(f"Research run completed in {elapsed:.2f}s with confidence: {report.confidence_level.value}")
        return report, plan, judge_eval, tracer
