"""Generate proof.json document from verification results."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from agent_see.models.proof import ConversionProof

logger = logging.getLogger(__name__)


def save_proof(proof: ConversionProof, output_dir: Path) -> Path:
    """Save the conversion proof as proof.json.

    This is the mathematical certificate that the conversion is correct.
    """
    proof_dir = output_dir / "proof"
    proof_dir.mkdir(parents=True, exist_ok=True)

    proof_path = proof_dir / "proof.json"
    proof_data = proof.model_dump(mode="json")
    proof_path.write_text(json.dumps(proof_data, indent=2, default=str))

    # Also generate a human-readable summary
    summary_path = proof_dir / "proof_summary.txt"
    summary = _generate_summary(proof)
    summary_path.write_text(summary)

    logger.info(f"Proof saved to {proof_path}")
    return proof_path


def _generate_summary(proof: ConversionProof) -> str:
    """Generate a human-readable summary of the proof."""
    lines = [
        "=" * 60,
        "AGENT-SEE CONVERSION PROOF",
        "=" * 60,
        "",
        f"Overall Status: {proof.overall_status.value}",
        f"Source: {proof.source_url or 'N/A'}",
        f"Timestamp: {proof.timestamp}",
        f"Source Hash: {proof.source_hash[:16]}...",
        "",
        "--- Coverage ---",
        f"  Original capabilities: {proof.coverage.original_count}",
        f"  Agent tools generated: {proof.coverage.agent_count}",
        f"  Successfully mapped: {proof.coverage.mapped_count}",
        f"  Coverage score: {proof.coverage.coverage_score:.2%}",
        f"  Gaps: {len(proof.coverage.gaps)}",
        f"  Extras (hallucinations): {len(proof.coverage.extras)}",
        "",
        "--- Fidelity ---",
        f"  Aggregate score: {proof.fidelity.aggregate_score:.3f}",
        f"  Target: >= {proof.fidelity.target}",
        f"  Status: {'PASS' if proof.fidelity.passes else 'FAIL'}",
        "",
        "--- Context Efficiency ---",
        f"  Interface tokens: {proof.context_efficiency.interface_tokens}",
        f"  Baseline tokens: {proof.context_efficiency.baseline_tokens}",
        f"  Compression ratio: {proof.context_efficiency.compression_ratio:.1f}x",
        "",
        "--- Hallucination Check ---",
        f"  Extra tools (no backing capability): {proof.hallucination_check.extras_count}",
        f"  Ungrounded capabilities: {proof.hallucination_check.ungrounded_count}",
        f"  Status: {proof.hallucination_check.status.value}",
        "",
    ]

    if proof.task_success:
        lines.extend(
            [
                "--- Task Success ---",
                f"  Total tasks: {proof.task_success.total_tasks}",
                f"  Passed: {proof.task_success.passed}",
                f"  Success rate: {proof.task_success.success_rate:.2%}",
                "",
            ]
        )

    if proof.composability:
        lines.extend(
            [
                "--- Composability ---",
                f"  Workflows tested: {proof.composability.workflows_tested}",
                f"  Workflows passed: {proof.composability.workflows_passed}",
                f"  Score: {proof.composability.composability_score:.2%}",
                "",
            ]
        )

    lines.append("=" * 60)
    return "\n".join(lines)
