"""Phase 5: Continuous Self-Improvement Loop.

Provides PerformanceRecord, PerformanceMonitor, AutoTriageRanker,
and OptimizationTrigger for autonomous telemetry monitoring, underperformance triage,
and threshold-driven self-evolution.
"""

from .monitor import PerformanceRecord, PerformanceMonitor
from .ranker import AutoTriageRanker, TriageTarget
from .trigger import OptimizationTask, OptimizationTrigger, TriggerRule, run_continuous_cycle

__all__ = [
    "PerformanceRecord",
    "PerformanceMonitor",
    "AutoTriageRanker",
    "TriageTarget",
    "OptimizationTask",
    "OptimizationTrigger",
    "TriggerRule",
    "run_continuous_cycle",
]
