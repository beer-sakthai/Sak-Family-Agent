"""Benchmark for dashboard JSON fact parsing in sakthai.dashboard.data."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from sakthai.dashboard.data import _parse_fact_json_batch  # type: ignore[attr-defined]


@dataclass
class DummyFact:
    id: int
    kind: str
    key: str | None
    value: str
    created_at: int
    tags: list[str]


def benchmark() -> None:
    # Build 1000 lead facts and 1000 revenue facts
    facts = [
        DummyFact(
            id=i,
            kind="revenue",
            key=f"Client_{i}",
            value=json.dumps(
                {
                    "client": f"Client_{i}",
                    "amount": 100.0 + i,
                    "type": "monthly" if i % 2 == 0 else "setup",
                    "date": "2025-01-15",
                }
            ),
            created_at=1700000000 + i,
            tags=[],
        )
        for i in range(1000)
    ]

    iterations = 500

    # Baseline parsing loop (individual json.loads inside loop)
    t0 = time.perf_counter()
    for _ in range(iterations):
        revenue_list_baseline: list[dict[str, Any]] = []
        for rf in facts:
            try:
                payload = json.loads(rf.value)
            except (TypeError, ValueError):
                payload = {
                    "client": rf.key or "Unknown",
                    "amount": 0.0,
                    "type": "setup",
                    "date": "",
                }
            revenue_list_baseline.append(payload)
    t1 = time.perf_counter()
    baseline_time = (t1 - t0) * 1000.0

    # Batch parsing loop
    t0 = time.perf_counter()
    for _ in range(iterations):
        revenue_list_batch: list[dict[str, Any]] = []
        parsed_payloads = _parse_fact_json_batch(facts)
        for rf, payload in zip(facts, parsed_payloads, strict=False):
            if not isinstance(payload, dict):
                payload = {
                    "client": rf.key or "Unknown",
                    "amount": 0.0,
                    "type": "setup",
                    "date": "",
                }
            revenue_list_batch.append(payload)
    t1 = time.perf_counter()
    batch_time = (t1 - t0) * 1000.0

    print(
        f"Baseline (Individual json.loads): {baseline_time:.2f} ms total ({baseline_time / iterations:.3f} ms/iter)"
    )
    print(
        f"Batch (_parse_fact_json_batch): {batch_time:.2f} ms total ({batch_time / iterations:.3f} ms/iter)"
    )
    speedup = ((baseline_time - batch_time) / baseline_time) * 100.0
    print(f"Improvement: {speedup:.2f}% faster")


if __name__ == "__main__":
    benchmark()
