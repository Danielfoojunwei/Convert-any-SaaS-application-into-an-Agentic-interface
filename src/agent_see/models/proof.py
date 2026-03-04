"""Verification and proof data models.

Every conversion produces a mathematical proof document (proof.json) that
certifies the generated agent interface is correct, complete, and faithful
to the original SaaS capabilities.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProofStatus(str, Enum):
    """Overall proof status."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"  # Passed with warnings (e.g., low-confidence capabilities)


class CapabilityMapping(BaseModel):
    """Maps an original capability to its generated agent tool."""

    original_capability_id: str
    original_name: str
    original_description: str
    agent_tool_name: str
    agent_tool_description: str
    param_jaccard: float = Field(
        ge=0.0, le=1.0, description="Parameter set overlap (Jaccard similarity)"
    )
    schema_match: float = Field(
        ge=0.0, le=1.0, description="Return schema structural match"
    )
    embedding_sim: float = Field(
        ge=0.0, le=1.0, description="Description embedding cosine similarity"
    )
    fidelity_score: float = Field(
        ge=0.0, le=1.0, description="Weighted composite fidelity score"
    )


class CoverageProof(BaseModel):
    """Mathematical proof of interface completeness.

    KEY INVARIANT: len(extras) == 0
    If the agent interface has capabilities NOT in the original SaaS,
    the system has hallucinated. This is a hard failure.
    """

    original_count: int = Field(description="Number of capabilities in original SaaS (|S|)")
    agent_count: int = Field(description="Number of tools in agent interface (|A|)")
    mapped_count: int = Field(description="Number of successfully mapped pairs (|S ∩ A|)")
    coverage_score: float = Field(
        ge=0.0, le=1.0, description="Coverage = |S ∩ A| / |S|"
    )
    gaps: list[str] = Field(
        default_factory=list, description="Capability IDs in S but not in A"
    )
    extras: list[str] = Field(
        default_factory=list,
        description="Tool names in A but not mapped to S (MUST be empty = no hallucinations)",
    )
    mappings: list[CapabilityMapping] = Field(default_factory=list)

    @property
    def has_hallucinations(self) -> bool:
        """If extras exist, the system has generated tools not backed by real capabilities."""
        return len(self.extras) > 0

    @property
    def is_complete(self) -> bool:
        return self.coverage_score == 1.0


class FidelityReport(BaseModel):
    """Semantic accuracy report: do the generated tools preserve original meanings?

    F(s, a) = α·ParamJaccard + β·SchemaMatch + γ·EmbeddingSim
    where α=0.4, β=0.4, γ=0.2
    """

    aggregate_score: float = Field(
        ge=0.0, le=1.0, description="Mean fidelity across all mappings"
    )
    per_capability: list[CapabilityMapping] = Field(default_factory=list)
    target: float = Field(default=0.95, description="Minimum acceptable fidelity")

    @property
    def passes(self) -> bool:
        return self.aggregate_score >= self.target


class TaskResult(BaseModel):
    """Result of a single synthetic task execution."""

    task_id: str
    task_description: str
    tool_name: str
    success: bool
    tokens_used: int = 0
    latency_ms: float = 0.0
    error: str | None = None
    run_number: int = 1


class TaskSuccessReport(BaseModel):
    """Empirical validation: how well do agents perform using the generated interface?

    pass@1 = first-attempt success rate
    pass^k = consistent success rate across k runs (measures reliability)
    """

    total_tasks: int
    passed: int
    failed: int
    success_rate: float = Field(description="passed / total")
    avg_tokens_per_task: float = Field(default=0.0, description="Context efficiency")
    avg_latency_ms: float = Field(default=0.0)
    pass_at_k: dict[int, float] = Field(
        default_factory=dict, description="pass@1, pass@3, pass@5"
    )
    pass_pow_k: dict[int, float] = Field(
        default_factory=dict, description="pass^1, pass^3, pass^5 (consistency)"
    )
    reliability_score: float = Field(
        default=0.0, description="1 - variance across runs"
    )
    results: list[TaskResult] = Field(default_factory=list)

    @property
    def passes(self) -> bool:
        """Target: pass@1 >= 0.9, pass^3 >= 0.8."""
        return self.pass_at_k.get(1, 0) >= 0.9 and self.pass_pow_k.get(3, 0) >= 0.8


class ContextEfficiencyReport(BaseModel):
    """How efficiently does the agent interface use the agent's context window?

    E ≈ TaskSuccessRate / TokensConsumed (vs naive baseline)
    """

    interface_tokens: int = Field(
        description="Total tokens to describe the agent interface"
    )
    baseline_tokens: int = Field(
        description="Tokens if raw API docs/site content were pasted into context"
    )
    compression_ratio: float = Field(
        description="baseline_tokens / interface_tokens (higher = more efficient)"
    )
    tasks_per_token: float = Field(
        default=0.0, description="TaskSuccessRate / interface_tokens"
    )


class ComposabilityReport(BaseModel):
    """How well do the generated tools work in multi-step workflows?

    Comp(A) = |successful_chains| / |attempted_chains|
    """

    workflows_tested: int
    workflows_passed: int
    composability_score: float = Field(
        ge=0.0, le=1.0, description="SuccessfulChains / AttemptedChains"
    )
    failed_workflows: list[str] = Field(
        default_factory=list, description="Names of workflows that failed"
    )
    target: float = Field(default=0.85)

    @property
    def passes(self) -> bool:
        return self.composability_score >= self.target


class HallucinationCheck(BaseModel):
    """Dedicated check for hallucinated (ungrounded) capabilities."""

    extras_count: int = Field(
        description="Tools in output not mapped to any real capability"
    )
    ungrounded_count: int = Field(
        description="Capabilities with empty or fabricated evidence"
    )
    status: ProofStatus

    @property
    def passes(self) -> bool:
        return self.extras_count == 0 and self.ungrounded_count == 0


class ConversionProof(BaseModel):
    """The complete mathematical proof document for a conversion.

    This is the final output artifact that certifies the generated agent
    interface is correct, complete, and faithful to the original SaaS.
    Saved as proof.json in the output directory.
    """

    coverage: CoverageProof
    fidelity: FidelityReport
    task_success: TaskSuccessReport | None = Field(
        default=None, description="None if empirical validation was skipped"
    )
    context_efficiency: ContextEfficiencyReport
    composability: ComposabilityReport | None = Field(
        default=None, description="None if no workflows to test"
    )
    hallucination_check: HallucinationCheck
    source_hash: str = Field(description="SHA-256 of all input sources")
    source_url: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_see_version: str = "0.1.0"
    overall_status: ProofStatus = ProofStatus.PASS

    def compute_overall_status(self) -> ProofStatus:
        """Determine overall proof status from sub-proofs."""
        if self.hallucination_check.extras_count > 0:
            return ProofStatus.FAIL  # Hard failure: hallucinations detected
        if self.hallucination_check.ungrounded_count > 0:
            return ProofStatus.FAIL
        if not self.coverage.is_complete:
            return ProofStatus.WARN  # Coverage gaps exist
        if not self.fidelity.passes:
            return ProofStatus.WARN
        return ProofStatus.PASS
