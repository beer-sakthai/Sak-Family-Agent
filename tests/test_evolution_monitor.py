"""Tests for Phase 5: Continuous Self-Improvement Loop (evolution.monitor)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from evolution.monitor import (
    AutoTriageRanker,
    OptimizationTask,
    OptimizationTrigger,
    PerformanceMonitor,
    PerformanceRecord,
    TriggerRule,
    run_continuous_cycle,
)


def test_performance_record_serialization() -> None:
    """Verify PerformanceRecord to_dict and from_dict roundtrip."""
    rec = PerformanceRecord(
        record_id="rec-1234",
        event_type="skill",
        name="github-code-review",
        success=True,
        latency_ms=120.5,
        metadata={"tokens": 450},
    )
    data = rec.to_dict()
    assert data["record_id"] == "rec-1234"
    assert data["event_type"] == "skill"
    assert data["latency_ms"] == 120.5

    restored = PerformanceRecord.from_dict(data)
    assert restored.record_id == rec.record_id
    assert restored.name == rec.name
    assert restored.success is True
    assert restored.latency_ms == 120.5


def test_performance_monitor_recording_and_metrics() -> None:
    """Verify recording events, querying history, and target aggregate metrics."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_file = Path(tmp_dir) / "metrics.json"
        monitor = PerformanceMonitor(storage_path=storage_file)

        # Record 4 events for 'file_tools' (3 success, 1 fail)
        monitor.record_event("tool", "file_tools", success=True, latency_ms=50.0)
        monitor.record_event("tool", "file_tools", success=True, latency_ms=60.0)
        monitor.record_event("tool", "file_tools", success=True, latency_ms=70.0)
        monitor.record_event(
            "tool", "file_tools", success=False, latency_ms=300.0, error_message="IOError"
        )

        # Record 2 events for 'web_tools' (2 success)
        monitor.record_event("tool", "web_tools", success=True, latency_ms=150.0)
        monitor.record_event("tool", "web_tools", success=True, latency_ms=200.0)

        history_file_tools = monitor.get_history(name="file_tools")
        assert len(history_file_tools) == 4

        metrics = monitor.get_target_metrics("tool", "file_tools")
        assert metrics["total_calls"] == 4
        assert metrics["success_count"] == 3
        assert metrics["failure_count"] == 1
        assert metrics["failure_rate"] == 0.25
        assert metrics["mean_latency_ms"] == 120.0
        assert metrics["p95_latency_ms"] >= 70.0

        summary = monitor.get_summary()
        assert summary["total_records"] == 6
        assert summary["total_failures"] == 1
        assert summary["targets_tracked"] == 2

        # Verify disk persistence
        monitor.save_to_disk()
        assert storage_file.exists()

        loaded_monitor = PerformanceMonitor(storage_path=storage_file)
        assert len(loaded_monitor.records) == 6


def test_auto_triage_ranker() -> None:
    """Verify AutoTriageRanker prioritizes high failure and high latency targets."""
    monitor = PerformanceMonitor(storage_path=None)

    # 1. Failing skill: 'failing_skill' with 3 failures out of 4 calls (75% failure rate)
    for _ in range(3):
        monitor.record_event("skill", "failing_skill", success=False, latency_ms=2500.0)
    monitor.record_event("skill", "failing_skill", success=True, latency_ms=400.0)

    # 2. Healthy skill: 'healthy_skill' with 5 successes
    for _ in range(5):
        monitor.record_event("skill", "healthy_skill", success=True, latency_ms=100.0)

    # 3. Degraded tool: 'slow_tool' with 100% success but very high latency (2200ms)
    for _ in range(4):
        monitor.record_event("tool", "slow_tool", success=True, latency_ms=2200.0)

    ranker = AutoTriageRanker()
    ranked = ranker.rank(monitor, min_calls=2)

    assert len(ranked) == 3
    # 'failing_skill' should be ranked highest due to high failure rate
    assert ranked[0].name == "failing_skill"
    assert ranked[0].failure_rate == 0.75
    assert ranked[0].triage_score > ranked[1].triage_score

    # 'healthy_skill' should be at the bottom
    assert ranked[-1].name == "healthy_skill"
    assert ranked[-1].failure_rate == 0.0


def test_optimization_trigger_and_dispatch() -> None:
    """Verify threshold evaluation and dispatch of optimization tasks."""
    monitor = PerformanceMonitor(storage_path=None)

    # Record 4 calls for 'unstable_skill', 2 failed (50% failure rate)
    monitor.record_event("skill", "unstable_skill", success=True, latency_ms=100.0)
    monitor.record_event("skill", "unstable_skill", success=True, latency_ms=120.0)
    monitor.record_event("skill", "unstable_skill", success=False, latency_ms=350.0)
    monitor.record_event("skill", "unstable_skill", success=False, latency_ms=400.0)

    # Record 4 calls for 'stable_skill', 0 failed
    for _ in range(4):
        monitor.record_event("skill", "stable_skill", success=True, latency_ms=80.0)

    rules = [
        TriggerRule(
            target_type="skill", min_calls=3, failure_threshold=0.20, latency_threshold_ms=2000.0
        )
    ]

    # Dry run trigger
    dry_tasks = run_continuous_cycle(monitor=monitor, rules=rules, dry_run=True)
    assert len(dry_tasks) == 1
    assert dry_tasks[0].target.name == "unstable_skill"
    assert dry_tasks[0].status == "DRY_RUN_TRIGGERED"
    assert "Failure rate 50.0%" in dry_tasks[0].rule_matched

    # Live dispatch with callback
    dispatched_ids = []

    def mock_dispatcher(task: OptimizationTask) -> bool:
        dispatched_ids.append(task.task_id)
        return True

    trigger = OptimizationTrigger(rules=rules, dispatch_callback=mock_dispatcher)
    live_tasks = trigger.run_cycle(monitor=monitor, dry_run=False)

    assert len(live_tasks) == 1
    assert live_tasks[0].status == "DISPATCHED"
    assert len(dispatched_ids) == 1
    assert dispatched_ids[0] == live_tasks[0].task_id
