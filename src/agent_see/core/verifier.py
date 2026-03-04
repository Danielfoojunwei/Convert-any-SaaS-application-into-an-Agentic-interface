"""Verification suite: prove the conversion is correct.

Computes all proof metrics:
- Coverage (completeness)
- Fidelity (semantic accuracy)
- Context efficiency
- Hallucination check
"""

from __future__ import annotations

import logging

from agent_see.models.capability import CapabilityGraph
from agent_see.models.proof import (
    CapabilityMapping,
    ContextEfficiencyReport,
    ConversionProof,
    CoverageProof,
    FidelityReport,
    HallucinationCheck,
    ProofStatus,
)
from agent_see.models.schema import ToolSchema

logger = logging.getLogger(__name__)

# Fidelity weights
ALPHA = 0.4  # Parameter match weight
BETA = 0.4  # Schema match weight
GAMMA = 0.2  # Embedding similarity weight


def _compute_param_jaccard(
    original_params: list[str],
    tool_params: list[str],
) -> float:
    """Jaccard similarity between parameter sets."""
    if not original_params and not tool_params:
        return 1.0  # Both empty = perfect match
    s1 = set(original_params)
    s2 = set(tool_params)
    intersection = s1 & s2
    union = s1 | s2
    if not union:
        return 1.0
    return len(intersection) / len(union)


def _compute_schema_match(
    original_fields: list[str],
    tool_fields: list[str],
) -> float:
    """Structural comparison of return schema fields."""
    if not original_fields and not tool_fields:
        return 1.0
    s1 = set(original_fields)
    s2 = set(tool_fields)
    if not s1 and not s2:
        return 1.0
    intersection = s1 & s2
    union = s1 | s2
    if not union:
        return 1.0
    return len(intersection) / len(union)


def _compute_embedding_sim(desc1: str, desc2: str) -> float:
    """Compute description similarity.

    Uses simple token overlap as a practical approximation.
    In production, this would use actual embeddings.
    """
    if not desc1 or not desc2:
        return 1.0 if desc1 == desc2 else 0.5

    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    if not words1 or not words2:
        return 0.5
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def verify_coverage(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
) -> CoverageProof:
    """Verify that the generated tools cover all original capabilities.

    C(S, A) = |S ∩ A| / |S|

    KEY INVARIANT: extras must be empty (no hallucinated tools).
    """
    original_ids = set(graph.nodes.keys())
    tool_cap_ids = {s.capability_id for s in tool_schemas}

    mapped = original_ids & tool_cap_ids
    gaps = original_ids - tool_cap_ids
    extras = tool_cap_ids - original_ids

    coverage_score = len(mapped) / len(original_ids) if original_ids else 1.0

    # Build mappings
    mappings = []
    tool_by_cap_id = {s.capability_id: s for s in tool_schemas}
    for cap_id in mapped:
        cap = graph.nodes[cap_id]
        tool = tool_by_cap_id[cap_id]

        param_jaccard = _compute_param_jaccard(
            [p.name for p in cap.parameters],
            [p.name for p in tool.parameters],
        )
        schema_match = _compute_schema_match(
            [f.name for f in cap.returns.fields],
            [f.name for f in tool.output_fields],
        )
        embedding_sim = _compute_embedding_sim(cap.description, tool.description)
        fidelity = ALPHA * param_jaccard + BETA * schema_match + GAMMA * embedding_sim

        mappings.append(
            CapabilityMapping(
                original_capability_id=cap_id,
                original_name=cap.name,
                original_description=cap.description,
                agent_tool_name=tool.name,
                agent_tool_description=tool.description,
                param_jaccard=param_jaccard,
                schema_match=schema_match,
                embedding_sim=embedding_sim,
                fidelity_score=fidelity,
            )
        )

    proof = CoverageProof(
        original_count=len(original_ids),
        agent_count=len(tool_schemas),
        mapped_count=len(mapped),
        coverage_score=coverage_score,
        gaps=list(gaps),
        extras=list(extras),
        mappings=mappings,
    )

    if proof.has_hallucinations:
        logger.error(
            f"HALLUCINATION DETECTED: {len(extras)} tools not mapped to real capabilities"
        )
    else:
        logger.info(f"Coverage: {coverage_score:.2%} ({len(mapped)}/{len(original_ids)})")

    return proof


def verify_fidelity(coverage_proof: CoverageProof) -> FidelityReport:
    """Compute aggregate fidelity from coverage proof mappings.

    F(S,A) = mean(F(s, M(s)) for all mappings)
    Target: F >= 0.95
    """
    if not coverage_proof.mappings:
        return FidelityReport(aggregate_score=1.0, per_capability=[])

    scores = [m.fidelity_score for m in coverage_proof.mappings]
    aggregate = sum(scores) / len(scores)

    report = FidelityReport(
        aggregate_score=aggregate,
        per_capability=coverage_proof.mappings,
    )

    logger.info(f"Fidelity: {aggregate:.3f} (target >= {report.target})")
    return report


def verify_context_efficiency(
    tool_schemas: list[ToolSchema],
    original_spec_tokens: int | None = None,
) -> ContextEfficiencyReport:
    """Measure context window efficiency.

    E = baseline_tokens / interface_tokens (compression ratio)
    """
    # Estimate interface tokens
    interface_tokens = sum(s.token_estimate for s in tool_schemas)

    # If we don't have original spec tokens, estimate from tool count
    if original_spec_tokens is None:
        # Rough estimate: raw API docs are ~5x more verbose than structured schemas
        original_spec_tokens = interface_tokens * 5

    compression_ratio = (
        original_spec_tokens / interface_tokens if interface_tokens > 0 else 1.0
    )

    report = ContextEfficiencyReport(
        interface_tokens=interface_tokens,
        baseline_tokens=original_spec_tokens,
        compression_ratio=compression_ratio,
    )

    logger.info(
        f"Context efficiency: {interface_tokens} tokens "
        f"(compression ratio: {compression_ratio:.1f}x)"
    )
    return report


def verify_no_hallucinations(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
    coverage_proof: CoverageProof,
) -> HallucinationCheck:
    """Dedicated hallucination check.

    Two checks:
    1. extras_count == 0 (no tools without backing capabilities)
    2. ungrounded_count == 0 (no capabilities with empty evidence)
    """
    extras_count = len(coverage_proof.extras)

    ungrounded_count = 0
    for cap in graph.nodes.values():
        if not cap.evidence or all(e.strip() == "" for e in cap.evidence):
            ungrounded_count += 1

    status = ProofStatus.PASS
    if extras_count > 0 or ungrounded_count > 0:
        status = ProofStatus.FAIL

    check = HallucinationCheck(
        extras_count=extras_count,
        ungrounded_count=ungrounded_count,
        status=status,
    )

    if check.passes:
        logger.info("Hallucination check: PASS")
    else:
        logger.error(
            f"Hallucination check: FAIL "
            f"(extras={extras_count}, ungrounded={ungrounded_count})"
        )

    return check


def run_full_verification(
    graph: CapabilityGraph,
    tool_schemas: list[ToolSchema],
    original_spec_tokens: int | None = None,
) -> ConversionProof:
    """Run the complete verification suite and produce a ConversionProof.

    This is the main entry point for verification.
    Returns a proof document ready to be saved as proof.json.
    """
    # 1. Coverage
    coverage = verify_coverage(graph, tool_schemas)

    # 2. Fidelity
    fidelity = verify_fidelity(coverage)

    # 3. Context efficiency
    context_efficiency = verify_context_efficiency(tool_schemas, original_spec_tokens)

    # 4. Hallucination check
    hallucination_check = verify_no_hallucinations(graph, tool_schemas, coverage)

    # Build proof
    proof = ConversionProof(
        coverage=coverage,
        fidelity=fidelity,
        task_success=None,  # Requires runtime agent execution
        context_efficiency=context_efficiency,
        composability=None,  # Requires runtime workflow testing
        hallucination_check=hallucination_check,
        source_hash=graph.source_hash,
        source_url=graph.source_url,
    )

    proof.overall_status = proof.compute_overall_status()

    logger.info(f"Verification complete: {proof.overall_status.value}")
    return proof
