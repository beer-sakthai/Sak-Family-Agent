"""Local model evaluation / MLOps logging.

Every ``run_agent`` call appends one :class:`EvalRecord` to a local JSONL file
(``eval_log_path()``, default ``sakthai_home()/eval.jsonl``) — model, provider,
latency, token usage, and outcome, with no cloud dependency. ``summarize_evals``
aggregates the log for ``sakthai eval summary``.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..config import eval_log_path, redact_secrets

logger = logging.getLogger(__name__)

_TASK_PREVIEW_LIMIT = 80


@dataclass(frozen=True)
class EvalRecord:
    timestamp: int
    task_preview: str
    model: str
    provider: str
    iterations: int
    stop_reason: str
    latency_s: float
    input_tokens: int
    output_tokens: int
    tool_call_count: int
    had_error: bool


def task_preview(task: str, limit: int = _TASK_PREVIEW_LIMIT) -> str:
    """Truncate a task string to a short, log-safe preview."""
    stripped = " ".join(task.split())
    return stripped if len(stripped) <= limit else stripped[: limit - 1] + "…"


def record_eval(record: EvalRecord, path: Path | None = None) -> None:
    """Append one eval record to the local JSONL log. Best-effort: never raises."""
    try:
        target = path or eval_log_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        line = redact_secrets(json.dumps(asdict(record), ensure_ascii=False)) + "\n"
        # Create with restricted permissions (rw-------), matching session logs.
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as exc:  # noqa: BLE001 — logging is best-effort
        logger.warning("Failed to record eval: %s", exc)


def _read_records(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or eval_log_path()
    if not target.exists():
        return []
    records = []
    for raw_line in target.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        try:
            records.append(json.loads(raw_line))
        except json.JSONDecodeError:
            continue
    return records


def summarize_evals(path: Path | None = None, limit: int = 50) -> dict[str, Any]:
    """Aggregate the most recent ``limit`` eval records: latency, tokens, errors, per-model."""
    records = _read_records(path)[-limit:]
    if not records:
        return {"count": 0}

    total = len(records)
    errors = sum(1 for r in records if r.get("had_error"))
    total_latency = sum(float(r.get("latency_s", 0.0)) for r in records)
    total_input = sum(int(r.get("input_tokens", 0)) for r in records)
    total_output = sum(int(r.get("output_tokens", 0)) for r in records)

    per_model: dict[str, dict[str, Any]] = {}
    for r in records:
        model = str(r.get("model", "unknown"))
        bucket = per_model.setdefault(
            model, {"count": 0, "_latency_total": 0.0, "input_tokens": 0, "output_tokens": 0}
        )
        bucket["count"] += 1
        bucket["_latency_total"] += float(r.get("latency_s", 0.0))
        bucket["input_tokens"] += int(r.get("input_tokens", 0))
        bucket["output_tokens"] += int(r.get("output_tokens", 0))
    for bucket in per_model.values():
        bucket["avg_latency_s"] = bucket["_latency_total"] / bucket["count"]
        del bucket["_latency_total"]

    return {
        "count": total,
        "error_rate": errors / total,
        "avg_latency_s": total_latency / total,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "per_model": per_model,
    }
