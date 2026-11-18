"""Continuous performance telemetry monitor for agent skills, tools, and prompts.

Tracks execution outcomes, error rates, and latency metrics across agent activities,
persisting telemetry records to JSON for auto-triage and threshold-triggered optimization.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class PerformanceRecord:
    """Telemetry record for an executed skill, tool, prompt, or benchmark."""

    record_id: str
    event_type: str  # "skill", "tool", "prompt", "benchmark"
    name: str
    success: bool
    latency_ms: float
    error_message: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert record to JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PerformanceRecord:
        """Create record from dictionary."""
        return cls(
            record_id=data["record_id"],
            event_type=data["event_type"],
            name=data["name"],
            success=data["success"],
            latency_ms=float(data["latency_ms"]),
            error_message=data.get("error_message"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            metadata=data.get("metadata", {}),
        )


class PerformanceMonitor:
    """In-memory telemetry buffer with persistent JSON backing."""

    def __init__(
        self,
        storage_path: str | Path | None = None,
        max_records: int = 5000,
    ) -> None:
        if storage_path:
            self.storage_path: Path | None = Path(storage_path).resolve()
        else:
            sakthai_home = os.getenv("SAKTHAI_HOME") or os.path.expanduser("~/.sakthai")
            self.storage_path = Path(sakthai_home) / "evolution_metrics.json"

        self.max_records = max(100, max_records)
        self.records: list[PerformanceRecord] = []
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        """Load records from disk if storage file exists."""
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.records = [PerformanceRecord.from_dict(d) for d in data][-self.max_records :]
            except Exception:
                self.records = []

    def save_to_disk(self) -> None:
        """Persist current records to disk."""
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        raw_list = [r.to_dict() for r in self.records]
        self.storage_path.write_text(json.dumps(raw_list, indent=2), encoding="utf-8")

    def record_event(
        self,
        event_type: str,
        name: str,
        success: bool,
        latency_ms: float,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
        persist: bool = False,
    ) -> PerformanceRecord:
        """Record an execution telemetry event."""
        rec = PerformanceRecord(
            record_id=str(uuid.uuid4())[:8],
            event_type=event_type,
            name=name,
            success=success,
            latency_ms=max(0.0, float(latency_ms)),
            error_message=error_message,
            metadata=metadata or {},
        )
        self.records.append(rec)
        if len(self.records) > self.max_records:
            self.records = self.records[-self.max_records :]

        if persist:
            self.save_to_disk()

        return rec

    def get_history(
        self,
        event_type: str | None = None,
        name: str | None = None,
        limit: int | None = None,
    ) -> list[PerformanceRecord]:
        """Retrieve filtered execution history."""
        filtered = self.records
        if event_type:
            filtered = [r for r in filtered if r.event_type == event_type]
        if name:
            filtered = [r for r in filtered if r.name == name]

        if limit is not None:
            return filtered[-limit:]
        return filtered

    def get_target_metrics(self, event_type: str, name: str) -> dict[str, Any]:
        """Compute aggregate metrics for a specific target."""
        matches = [r for r in self.records if r.event_type == event_type and r.name == name]
        total_calls = len(matches)
        if total_calls == 0:
            return {
                "event_type": event_type,
                "name": name,
                "total_calls": 0,
                "success_count": 0,
                "failure_count": 0,
                "failure_rate": 0.0,
                "mean_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
            }

        success_count = sum(1 for r in matches if r.success)
        failure_count = total_calls - success_count
        failure_rate = failure_count / total_calls

        latencies = sorted(r.latency_ms for r in matches)
        mean_latency = sum(latencies) / total_calls
        p95_idx = int(0.95 * total_calls)
        p95_latency = latencies[min(p95_idx, total_calls - 1)]

        return {
            "event_type": event_type,
            "name": name,
            "total_calls": total_calls,
            "success_count": success_count,
            "failure_count": failure_count,
            "failure_rate": failure_rate,
            "mean_latency_ms": mean_latency,
            "p95_latency_ms": p95_latency,
        }

    def get_all_target_summaries(self) -> list[dict[str, Any]]:
        """Return metrics for all unique target (event_type, name) pairs."""
        pairs = {(r.event_type, r.name) for r in self.records}
        return [self.get_target_metrics(event_type, name) for event_type, name in sorted(pairs)]

    def get_summary(self) -> dict[str, Any]:
        """Return overall system telemetry summary."""
        total_records = len(self.records)
        total_success = sum(1 for r in self.records if r.success)
        total_failures = total_records - total_success
        overall_failure_rate = (total_failures / total_records) if total_records > 0 else 0.0

        return {
            "total_records": total_records,
            "total_success": total_success,
            "total_failures": total_failures,
            "overall_failure_rate": overall_failure_rate,
            "targets_tracked": len({(r.event_type, r.name) for r in self.records}),
        }
