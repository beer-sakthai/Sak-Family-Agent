"""Continuous optimization trigger for automated self-improvement.

Monitors execution telemetry, evaluates threshold rules (failure rate, latency degradation),
and dispatches targeted evolution jobs for skills, tools, and prompts.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table

from .monitor import PerformanceMonitor
from .ranker import AutoTriageRanker, TriageTarget

console = Console()


@dataclass
class TriggerRule:
    """Threshold rule for triggering automated optimization."""

    target_type: str = "all"  # "skill", "tool", "prompt", "all"
    min_calls: int = 3
    failure_threshold: float = 0.20  # Trigger if failure rate >= 20%
    latency_threshold_ms: float = 2000.0  # Trigger if p95 latency >= 2000ms


@dataclass
class OptimizationTask:
    """An optimization task triggered by rule violations."""

    task_id: str
    target: TriageTarget
    rule_matched: str
    status: str = "PENDING"  # "PENDING", "DISPATCHED", "COMPLETED", "FAILED"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OptimizationTrigger:
    """Evaluates telemetry rules and dispatches optimization jobs."""

    def __init__(
        self,
        rules: list[TriggerRule] | None = None,
        ranker: AutoTriageRanker | None = None,
        dispatch_callback: Callable[[OptimizationTask], bool] | None = None,
    ) -> None:
        self.rules = rules or [
            TriggerRule(target_type="skill", min_calls=3, failure_threshold=0.20, latency_threshold_ms=2500.0),
            TriggerRule(target_type="tool", min_calls=3, failure_threshold=0.15, latency_threshold_ms=1500.0),
            TriggerRule(target_type="prompt", min_calls=3, failure_threshold=0.25, latency_threshold_ms=3000.0),
        ]
        self.ranker = ranker or AutoTriageRanker()
        self.dispatch_callback = dispatch_callback
        self.task_history: list[OptimizationTask] = []

    def evaluate_target_against_rules(self, target: TriageTarget) -> str | None:
        """Check if target violates any active rule and return violation description."""
        for rule in self.rules:
            if rule.target_type != "all" and rule.target_type != target.target_type:
                continue

            if target.total_calls < rule.min_calls:
                continue

            if target.failure_rate >= rule.failure_threshold:
                return (
                    f"Failure rate {target.failure_rate:.1%} exceeds threshold {rule.failure_threshold:.1%}"
                )

            if target.latency_p95_ms >= rule.latency_threshold_ms:
                return (
                    f"Tail latency {target.latency_p95_ms:.1f}ms exceeds threshold {rule.latency_threshold_ms:.1f}ms"
                )

        return None

    def run_cycle(
        self,
        monitor: PerformanceMonitor,
        dry_run: bool = True,
    ) -> list[OptimizationTask]:
        """Execute a continuous evaluation and triggering cycle."""
        ranked = self.ranker.rank(monitor, min_calls=1)
        generated_tasks: list[OptimizationTask] = []

        for target in ranked:
            violation = self.evaluate_target_against_rules(target)
            if violation:
                task = OptimizationTask(
                    task_id=f"opt-{uuid.uuid4().hex[:8]}",
                    target=target,
                    rule_matched=violation,
                    status="PENDING",
                )

                if not dry_run and self.dispatch_callback:
                    try:
                        dispatched = self.dispatch_callback(task)
                        task.status = "DISPATCHED" if dispatched else "FAILED"
                    except Exception:
                        task.status = "FAILED"
                elif dry_run:
                    task.status = "DRY_RUN_TRIGGERED"

                generated_tasks.append(task)
                self.task_history.append(task)

        return generated_tasks


def run_continuous_cycle(
    monitor: PerformanceMonitor,
    rules: list[TriggerRule] | None = None,
    dry_run: bool = True,
) -> list[OptimizationTask]:
    """Helper to run a continuous optimization cycle on a monitor."""
    trigger = OptimizationTrigger(rules=rules)
    return trigger.run_cycle(monitor=monitor, dry_run=dry_run)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for continuous optimization trigger."""
    parser = argparse.ArgumentParser(description="Continuous Self-Improvement Optimization Trigger")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate trigger without dispatching")
    parser.add_argument("--storage-path", type=str, default=None, help="Custom path to metrics file")

    args = parser.parse_args(argv)

    monitor = PerformanceMonitor(storage_path=args.storage_path)
    trigger = OptimizationTrigger()
    tasks = trigger.run_cycle(monitor=monitor, dry_run=args.dry_run)

    table = Table(title="Continuous Optimization Trigger: Cycle Results")
    table.add_column("Task ID", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Target", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Reason", style="white")

    for task in tasks:
        table.add_row(
            task.task_id,
            task.target.target_type,
            task.target.name,
            task.status,
            task.rule_matched,
        )

    console.print(table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
