"""Auto-triage ranker for identifying underperforming agent artifacts.

Evaluates failure frequency, failure rate, and tail latency (p95) degradation
to prioritize targets (skills, tools, prompts) for continuous evolutionary optimization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitor import PerformanceMonitor


@dataclass
class TriageTarget:
    """Prioritized candidate for evolutionary self-improvement."""

    target_type: str  # "skill", "tool", "prompt"
    name: str
    failure_rate: float
    latency_p95_ms: float
    total_calls: int
    triage_score: float
    reason: str


class AutoTriageRanker:
    """Ranks candidate optimization targets by impact x failure severity."""

    def __init__(
        self,
        failure_weight: float = 0.70,
        latency_weight: float = 0.30,
        latency_baseline_ms: float = 200.0,
        latency_degradation_cap_ms: float = 2000.0,
    ) -> None:
        self.failure_weight = failure_weight
        self.latency_weight = latency_weight
        self.latency_baseline_ms = max(1.0, latency_baseline_ms)
        self.latency_degradation_cap_ms = max(self.latency_baseline_ms + 1.0, latency_degradation_cap_ms)

    def calculate_target_score(self, summary: dict[str, Any]) -> tuple[float, str]:
        """Calculate composite triage priority score and explanation."""
        total_calls = summary["total_calls"]
        failure_rate = summary["failure_rate"]
        p95_latency = summary["p95_latency_ms"]

        if total_calls == 0:
            return 0.0, "No calls recorded"

        # Failure penalty (0.0 to 1.0)
        failure_penalty = failure_rate

        # Normalized latency penalty (0.0 to 1.0)
        excess_latency = max(0.0, p95_latency - self.latency_baseline_ms)
        span = self.latency_degradation_cap_ms - self.latency_baseline_ms
        latency_penalty = min(1.0, excess_latency / span)

        raw_severity = (self.failure_weight * failure_penalty) + (self.latency_weight * latency_penalty)

        # Frequency factor scales with total usage: min(2.0, 0.5 + 0.1 * total_calls)
        frequency_factor = min(2.0, 0.5 + 0.1 * total_calls)

        triage_score = raw_severity * frequency_factor

        # Formulate reason
        reasons = []
        if failure_rate > 0.10:
            reasons.append(f"High failure rate ({failure_rate:.1%})")
        if p95_latency > self.latency_baseline_ms * 2.0:
            reasons.append(f"Elevated tail latency (p95: {p95_latency:.1f}ms)")
        if not reasons:
            reasons.append("Nominal performance; low optimization priority")

        return max(0.0, triage_score), "; ".join(reasons)

    def rank(
        self,
        monitor: PerformanceMonitor,
        min_calls: int = 1,
        target_type: str | None = None,
    ) -> list[TriageTarget]:
        """Return prioritized list of underperforming targets."""
        summaries = monitor.get_all_target_summaries()
        ranked_targets: list[TriageTarget] = []

        for summary in summaries:
            if summary["total_calls"] < min_calls:
                continue
            if target_type and summary["event_type"] != target_type:
                continue

            score, reason = self.calculate_target_score(summary)
            target = TriageTarget(
                target_type=summary["event_type"],
                name=summary["name"],
                failure_rate=summary["failure_rate"],
                latency_p95_ms=summary["p95_latency_ms"],
                total_calls=summary["total_calls"],
                triage_score=score,
                reason=reason,
            )
            ranked_targets.append(target)

        # Sort descending by triage score
        ranked_targets.sort(key=lambda t: t.triage_score, reverse=True)
        return ranked_targets
