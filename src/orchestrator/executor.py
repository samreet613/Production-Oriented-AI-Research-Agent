"""Plan execution engine: coordinates tool dispatches with error isolation and status updates."""

import logging
from typing import List, Optional, Tuple
from src.models import ResearchPlan, RawToolOutput, PlanStep
from src.tools.registry import ToolRegistry
from src.tracer import ResearchTracer

logger = logging.getLogger("research_agent.executor")


class PlanExecutor:
    """Executes research plans step-by-step with resilience and progress tracking."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_plan(
        self,
        plan: ResearchPlan,
        tracer: Optional[ResearchTracer] = None
    ) -> Tuple[ResearchPlan, List[RawToolOutput]]:
        """Executes all steps in the plan and returns updated plan + collected tool outputs."""
        outputs: List[RawToolOutput] = []

        for step in plan.steps:
            step.status = "running"
            logger.info(f"Executing Step {step.step_id}: [{step.tool.value}] - '{step.query_or_target}'")

            tool = self.registry.get(step.tool.value)
            if not tool:
                err_msg = f"Tool '{step.tool.value}' is not registered in ToolRegistry."
                logger.error(err_msg)
                step.status = "failed"
                step.error = err_msg
                outputs.append(RawToolOutput(
                    tool_name=step.tool.value,
                    query_or_target=step.query_or_target,
                    success=False,
                    error=err_msg
                ))
                continue

            # Execute tool safely
            raw_output = tool.execute(step.query_or_target, tracer=tracer)
            outputs.append(raw_output)

            if raw_output.success:
                step.status = "completed"
                # Generate a short evidence summary for the plan step
                if isinstance(raw_output.data, list) and len(raw_output.data) > 0:
                    first_item = raw_output.data[0]
                    step.result_summary = f"Retrieved {len(raw_output.data)} items. Top: {first_item.get('title', '')[:50]}"
                elif isinstance(raw_output.data, dict):
                    step.result_summary = f"Scraped {raw_output.data.get('char_count', 0)} characters from {raw_output.data.get('title', '')[:40]}"
                else:
                    step.result_summary = "Retrieved unstructured evidence."
            else:
                step.status = "failed"
                step.error = raw_output.error
                step.result_summary = f"Failed: {raw_output.error}"

        return plan, outputs
