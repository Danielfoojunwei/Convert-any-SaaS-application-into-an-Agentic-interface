"""CLEAR metrics framework for evaluating agent interface quality.

CLEAR = Cost, Latency, Efficacy, Assurance, Reliability
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from agent_see.models.proof import TaskResult


@dataclass
class CLEARMetrics:
    """The five dimensions of agent interface quality."""

    cost: float  # Average tokens per task
    latency: float  # Average latency in ms
    efficacy: float  # Task completion rate (0-1)
    assurance: float  # Confidence in results (0-1)
    reliability: float  # Consistency across runs (0-1)


def compute_clear_metrics(results: list[TaskResult]) -> CLEARMetrics:
    """Compute CLEAR metrics from task execution results."""
    if not results:
        return CLEARMetrics(
            cost=0, latency=0, efficacy=0, assurance=0, reliability=0
        )

    # Cost: average tokens per task
    cost = statistics.mean(r.tokens_used for r in results) if results else 0

    # Latency: average latency
    latency = statistics.mean(r.latency_ms for r in results) if results else 0

    # Efficacy: success rate
    successes = sum(1 for r in results if r.success)
    efficacy = successes / len(results)

    # Assurance: based on success consistency
    assurance = efficacy  # Simple approximation

    # Reliability: 1 - coefficient of variation of success across runs
    if len(results) > 1:
        success_values = [1.0 if r.success else 0.0 for r in results]
        mean = statistics.mean(success_values)
        if mean > 0:
            stdev = statistics.stdev(success_values)
            reliability = max(0, 1 - (stdev / mean))
        else:
            reliability = 0.0
    else:
        reliability = efficacy

    return CLEARMetrics(
        cost=cost,
        latency=latency,
        efficacy=efficacy,
        assurance=assurance,
        reliability=reliability,
    )


def compute_pass_at_k(
    results_by_task: dict[str, list[TaskResult]],
    k: int = 1,
) -> float:
    """Compute pass@k: fraction of tasks where at least one of k attempts succeeds.

    pass@1 = first-attempt success rate (most important metric).
    """
    if not results_by_task:
        return 0.0

    passes = 0
    for task_id, runs in results_by_task.items():
        first_k = runs[:k]
        if any(r.success for r in first_k):
            passes += 1

    return passes / len(results_by_task)


def compute_pass_pow_k(
    results_by_task: dict[str, list[TaskResult]],
    k: int = 3,
) -> float:
    """Compute pass^k: fraction of tasks where ALL k attempts succeed.

    pass^3 measures consistency: agent succeeds reliably, not just sometimes.
    Gap between pass@k and pass^k reveals non-determinism.
    """
    if not results_by_task:
        return 0.0

    passes = 0
    for task_id, runs in results_by_task.items():
        first_k = runs[:k]
        if len(first_k) >= k and all(r.success for r in first_k):
            passes += 1

    return passes / len(results_by_task)
