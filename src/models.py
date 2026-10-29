"""Pydantic data models for structured inputs, plans, tool outputs, and synthesis."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """Confidence level assigned to the synthesized research findings."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ToolType(str, Enum):
    """Available tools in the research agent system."""
    WEB_SEARCH = "web_search"
    WEB_SCRAPER = "web_scraper"
    ACADEMIC_SEARCH = "academic_search"
    KNOWLEDGE_RETRIEVER = "knowledge_retriever"


class PlanStep(BaseModel):
    """Represents an individual step within the research plan."""
    step_id: int = Field(description="Step index (1-based)")
    objective: str = Field(description="Sub-question or purpose of this step")
    tool: ToolType = Field(description="Tool selected for this step")
    query_or_target: str = Field(description="Search query or target URL")
    rationale: str = Field(description="Why this tool and query were chosen")
    status: str = Field(default="pending", description="Status: pending, running, completed, failed")
    result_summary: Optional[str] = Field(default=None, description="Summary of evidence gathered")
    error: Optional[str] = Field(default=None, description="Error message if step failed")


class ResearchPlan(BaseModel):
    """The structured plan produced prior to tool execution."""
    original_query: str = Field(description="The original user question")
    intent_analysis: str = Field(description="Deconstructed problem formulation and scope")
    steps: List[PlanStep] = Field(description="Ordered list of execution steps")
    estimated_complexity: str = Field(default="Medium", description="Estimated research complexity (Low/Medium/High)")


class SourceItem(BaseModel):
    """A citation source backing a finding."""
    source_id: int = Field(description="Citation index e.g. 1 for [1]")
    title: str = Field(description="Title of page, paper, or document")
    url: str = Field(description="Direct URL or identifier")
    snippet: str = Field(description="Key relevant excerpt or summary from the source")
    domain: Optional[str] = Field(default=None, description="Domain name (e.g. github.com, arxiv.org)")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score (0.0 to 1.0)")


class RawToolOutput(BaseModel):
    """Raw output received from tool execution before filtering."""
    tool_name: str
    query_or_target: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    latency_seconds: float = 0.0
    retries_used: int = 0
    from_cache: bool = False


class FilteredEvidence(BaseModel):
    """Evidence item after filtering noisy, duplicate, or weak content."""
    source_title: str
    source_url: str
    relevant_content: str
    step_objective: str
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)


class GroundingEvaluation(BaseModel):
    """Evaluation result assessing factual alignment of output with gathered sources."""
    grounded_claims: List[str] = Field(default_factory=list, description="Claims directly supported by sources")
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims lacking direct source support")
    grounding_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Ratio of grounded claims")
    verdict: str = Field(default="Pass", description="Pass, Caution, or Fail")
    audit_notes: str = Field(default="", description="Audit explanation from the evaluator")


class ResearchReport(BaseModel):
    """The final structured output meeting all functional expectations."""
    user_question: str = Field(description="The original user inquiry")
    short_answer: str = Field(description="Concise executive summary answering the core question")
    key_findings: List[str] = Field(description="Detailed bullet points backed by citations like [1], [2]")
    sources_used: List[SourceItem] = Field(description="Complete list of referenced sources")
    confidence_level: ConfidenceLevel = Field(description="Confidence rating: High, Medium, or Low")
    confidence_rationale: str = Field(description="Explanation of why this confidence level was assigned")
    limitations_or_assumptions: List[str] = Field(description="Explicit constraints, data gaps, or assumptions")
    suggested_next_steps: List[str] = Field(description="Follow-up research directions or technical actions")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics including latency, plan steps, tools executed, and grounding score"
    )
