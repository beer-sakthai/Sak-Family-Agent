"""High-Concurrency Benchmarks & Real-Time Telemetry Engine for the SakThai Runtime Gateway.

Provides concurrent throughput benchmarking (TTFT, tokens/sec, latency percentiles)
and live runtime telemetry collection.
"""

from __future__ import annotations

import concurrent.futures
import statistics
import time
from collections import deque
from collections.abc import Generator
from typing import Any

from .router import GatewayRouter


class GatewayTelemetryTracker:
    """Tracks live request latencies, token throughput, and guardrail blocks."""

    def __init__(self, max_samples: int = 500) -> None:
        self._start_time = time.time()
        self.total_requests = 0
        self.total_tokens = 0
        self.total_errors = 0
        self.guardrail_blocks = 0
        self._latencies_ms: deque[float] = deque(maxlen=max_samples)
        self._ttft_ms: deque[float] = deque(maxlen=max_samples)

    def record_request(
        self,
        latency_ms: float,
        *,
        ttft_ms: float | None = None,
        tokens: int = 0,
        error: bool = False,
        blocked: bool = False,
    ) -> None:
        """Record metrics for a completed gateway request."""
        self.total_requests += 1
        self.total_tokens += max(0, tokens)
        if error:
            self.total_errors += 1
        if blocked:
            self.guardrail_blocks += 1
        self._latencies_ms.append(max(0.01, latency_ms))
        if ttft_ms is not None:
            self._ttft_ms.append(max(0.01, ttft_ms))

    def snapshot(self) -> dict[str, Any]:
        """Return aggregated real-time telemetry metrics and percentiles."""
        uptime = max(0.001, time.time() - self._start_time)
        lats = sorted(self._latencies_ms)
        ttfts = sorted(self._ttft_ms)

        def _pct(arr: list[float], q: float) -> float:
            if not arr:
                return 0.0
            idx = min(len(arr) - 1, max(0, int(len(arr) * q)))
            return round(arr[idx], 2)

        avg_lat = round(statistics.mean(lats), 2) if lats else 0.0
        avg_ttft = round(statistics.mean(ttfts), 2) if ttfts else 0.0
        rps = round(self.total_requests / uptime, 2)
        tps = round(self.total_tokens / uptime, 2)

        return {
            "ok": True,
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_errors": self.total_errors,
            "guardrail_blocks": self.guardrail_blocks,
            "requests_per_sec": rps,
            "tokens_per_sec": tps,
            "latency_ms": {
                "avg": avg_lat,
                "p50": _pct(lats, 0.50),
                "p95": _pct(lats, 0.95),
                "p99": _pct(lats, 0.99),
            },
            "ttft_ms": {
                "avg": avg_ttft,
                "p50": _pct(ttfts, 0.50),
                "p95": _pct(ttfts, 0.95),
                "p99": _pct(ttfts, 0.99),
            },
        }


def run_gateway_benchmark(
    router: GatewayRouter | None = None,
    *,
    concurrency: int = 10,
    num_requests: int = 50,
    persona: str = "sakjules",
    stream: bool = True,
    prompt: str = "Benchmark probe: verify runtime throughput and TTFT.",
) -> dict[str, Any]:
    """Execute a high-concurrency benchmark suite against the GatewayRouter."""
    active_router = router or GatewayRouter()
    concurrency = max(1, min(100, int(concurrency)))
    num_requests = max(1, min(2000, int(num_requests)))

    latencies: list[float] = []
    ttfts: list[float] = []
    token_counts: list[int] = []
    errors = 0

    def _worker(idx: int) -> tuple[float, float, int, bool]:
        req_start = time.perf_counter()
        first_token_ts: float | None = None
        tokens = 0
        try:
            body = {
                "model": persona,
                "stream": stream,
                "disable_memory": True,
                "messages": [{"role": "user", "content": f"{prompt} [req-{idx}]"}],
            }
            res, is_stream = active_router.handle_chat_completion(
                body, headers={"x-sakthai-disable-memory": "true"}
            )
            if is_stream and isinstance(res, Generator):
                for chunk in res:
                    if first_token_ts is None:
                        first_token_ts = time.perf_counter()
                    if "delta" in chunk:
                        tokens += 1
            elif isinstance(res, dict):
                first_token_ts = time.perf_counter()
                tokens = int(res.get("usage", {}).get("completion_tokens", 1))
            end_ts = time.perf_counter()
            total_ms = (end_ts - req_start) * 1000.0
            ttft_ms = ((first_token_ts or end_ts) - req_start) * 1000.0
            return total_ms, ttft_ms, max(1, tokens), False
        except Exception:
            end_ts = time.perf_counter()
            total_ms = (end_ts - req_start) * 1000.0
            return total_ms, total_ms, 0, True

    bench_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(_worker, i) for i in range(num_requests)]
        for fut in concurrent.futures.as_completed(futures):
            lat_ms, ttft_ms, tok, err = fut.result()
            latencies.append(lat_ms)
            ttfts.append(ttft_ms)
            token_counts.append(tok)
            if err:
                errors += 1

    wall_sec = max(0.0001, time.perf_counter() - bench_start)
    lats_sorted = sorted(latencies)
    ttfts_sorted = sorted(ttfts)
    total_toks = sum(token_counts)

    def _p(arr: list[float], q: float) -> float:
        if not arr:
            return 0.0
        idx = min(len(arr) - 1, max(0, int(len(arr) * q)))
        return round(arr[idx], 2)

    return {
        "ok": errors == 0,
        "persona": persona,
        "stream": stream,
        "concurrency": concurrency,
        "requests": num_requests,
        "errors": errors,
        "wall_time_ms": round(wall_sec * 1000.0, 2),
        "requests_per_sec": round(num_requests / wall_sec, 2),
        "total_tokens": total_toks,
        "tokens_per_sec": round(total_toks / wall_sec, 2),
        "latency_ms": {
            "avg": round(statistics.mean(lats_sorted), 2),
            "p50": _p(lats_sorted, 0.50),
            "p95": _p(lats_sorted, 0.95),
            "p99": _p(lats_sorted, 0.99),
        },
        "ttft_ms": {
            "avg": round(statistics.mean(ttfts_sorted), 2),
            "p50": _p(ttfts_sorted, 0.50),
            "p95": _p(ttfts_sorted, 0.95),
            "p99": _p(ttfts_sorted, 0.99),
        },
    }
