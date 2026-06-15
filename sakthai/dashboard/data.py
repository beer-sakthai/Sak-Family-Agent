"""Data layer for the dashboard.

:func:`collect_dashboard_data` reads the SQLite memory store and assembles an
honest snapshot of what's actually there — KPIs, a cumulative growth series,
recent facts, top observations, and a per-kind category breakdown. On an empty
or unreadable store it returns a small ``demo`` sample so the UI still renders,
with ``source`` flagging which case occurred.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_LIVE = "live"
SOURCE_DEMO = "demo"

# Generous read caps: enough to cover a real store without unbounded loads.
_FACTS_LIMIT = 1000
_OBS_LIMIT = 200

_DAY = 86_400
_WEEK = 7 * _DAY

# Per-kind colours for the category breakdown; unknown kinds cycle the fallback.
_KIND_COLORS = {
    "pref": "#a855f7",
    "preference": "#a855f7",
    "note": "#3b82f6",
    "fact": "#22d3ee",
    "project": "#34d399",
    "profile": "#34d399",
    "skill": "#f59e0b",
    "decision": "#f472b6",
    "lesson": "#f59e0b",
}
_FALLBACK_COLORS = ["#a855f7", "#3b82f6", "#22d3ee", "#f472b6", "#34d399", "#f59e0b"]

DEMO_DATA: dict[str, Any] = {
    "generated_at": "demo",
    "source": SOURCE_DEMO,
    "kpis": {
        "total_facts": 5,
        "total_facts_delta": 5,
        "total_observations": 2,
        "total_observations_delta": 2,
    },
    "growth": {
        "labels": [f"Day {i}" for i in range(1, 8)],
        "facts": [1, 2, 2, 3, 4, 4, 5],
        "observations": [0, 0, 1, 1, 1, 2, 2],
    },
    "recent_facts": [
        {"id": 5, "kind": "pref", "key": "language", "value": "Python", "created": "demo"},
        {"id": 4, "kind": "pref", "key": "editor", "value": "VS Code", "created": "demo"},
        {"id": 3, "kind": "profile", "key": "timezone", "value": "Asia/Bangkok", "created": "demo"},
        {"id": 2, "kind": "note", "key": "", "value": "Prefers concise replies", "created": "demo"},
        {"id": 1, "kind": "project", "key": "", "value": "Building SakThai", "created": "demo"},
    ],
    "top_observations": [
        {"summary": "Prefers Python for data tasks", "weight": 0.95},
        {"summary": "Most active in the evening", "weight": 0.80},
    ],
    "categories": [
        {"name": "Pref", "count": 2, "color": _KIND_COLORS["pref"]},
        {"name": "Profile", "count": 1, "color": _KIND_COLORS["profile"]},
        {"name": "Note", "count": 1, "color": _KIND_COLORS["note"]},
        {"name": "Project", "count": 1, "color": _KIND_COLORS["project"]},
        {"name": "Observations", "count": 2, "color": "#f472b6"},
    ],
}


def _fmt_date(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


def _color_for(kind: str, index: int) -> str:
    return _KIND_COLORS.get(kind, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])


def collect_dashboard_data(db_path: Path | None = None, days: int = 30) -> dict[str, Any]:
    """Assemble a dashboard snapshot from the memory store, or demo data if empty."""
    try:
        from sakthai.memory.store import MemoryStore

        with MemoryStore(db_path) as store:
            facts = store.list_facts(limit=_FACTS_LIMIT)
            observations = store.top_observations(limit=_OBS_LIMIT)
    except Exception as exc:  # noqa: BLE001 — unreadable store → demo data
        logger.warning("Could not read MemoryStore (%s); using demo data", exc)
        return dict(DEMO_DATA)

    if not facts and not observations:
        return dict(DEMO_DATA)

    now = int(time.time())
    week_ago = now - _WEEK
    facts_this_week = sum(1 for f in facts if f.created_at >= week_ago)
    obs_this_week = sum(1 for o in observations if o.created_at >= week_ago)

    start = now - days * _DAY
    labels: list[str] = []
    fact_series: list[int] = []
    obs_series: list[int] = []
    for d in range(days):
        day_end = start + (d + 1) * _DAY
        labels.append(_fmt_date(day_end - _DAY))
        # Inclusive: the final bucket ends at `now`, so facts created this very
        # second still count toward the latest cumulative total.
        fact_series.append(sum(1 for f in facts if f.created_at <= day_end))
        obs_series.append(sum(1 for o in observations if o.created_at <= day_end))

    counts: dict[str, int] = {}
    for f in facts:
        counts[f.kind] = counts.get(f.kind, 0) + 1
    categories: list[dict[str, Any]] = [
        {
            "name": kind.replace("_", " ").title(),
            "count": count,
            "color": _color_for(kind, i),
        }
        for i, (kind, count) in enumerate(sorted(counts.items(), key=lambda kv: -kv[1]))
    ]
    if observations:
        categories.append({"name": "Observations", "count": len(observations), "color": "#f472b6"})

    return {
        "generated_at": _fmt_date(now),
        "source": SOURCE_LIVE,
        "kpis": {
            "total_facts": len(facts),
            "total_facts_delta": facts_this_week,
            "total_observations": len(observations),
            "total_observations_delta": obs_this_week,
        },
        "growth": {"labels": labels, "facts": fact_series, "observations": obs_series},
        "recent_facts": [
            {
                "id": f.id,
                "kind": f.kind,
                "key": f.key or "",
                "value": f.value,
                "created": _fmt_date(f.created_at),
            }
            for f in facts[:8]
        ],
        "top_observations": [
            {"summary": o.summary, "weight": round(o.weight, 2)} for o in observations[:6]
        ],
        "categories": categories,
    }


_SESSIONS_SCAN_LIMIT = 5000
_RECENT_SESSIONS = 20
_TASK_PREVIEW_CHARS = 80


def _load_session(path: Path) -> dict[str, Any] | None:
    """Load one session-log JSON, returning None on any read/parse failure."""
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        data = None
    return data if isinstance(data, dict) else None


def collect_session_data(sessions_path: Path | None = None) -> dict[str, Any]:
    """Aggregate the agent session logs into a dashboard-ready snapshot.

    Reads the JSON logs ``run_agent`` writes (task/model/usage/timestamp),
    aggregating sessions and token usage by day and by model, plus a list of the
    most recent runs. Returns ``source: "empty"`` with zeroed structures when
    there are no readable logs, so the UI always has something to render.
    """
    from sakthai.config import sessions_dir

    base = Path(sessions_path) if sessions_path is not None else sessions_dir()
    empty: dict[str, Any] = {
        "source": "empty",
        "totals": {"sessions": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "by_day": {"labels": [], "sessions": [], "tokens": []},
        "by_model": [],
        "recent_sessions": [],
    }
    if not base.is_dir():
        return empty

    sessions: list[dict[str, Any]] = []
    for path in sorted(base.glob("*.json"), reverse=True)[:_SESSIONS_SCAN_LIMIT]:
        data = _load_session(path)
        if data is None:
            continue
        usage = data.get("usage") or {}
        result = data.get("result") or {}
        ts = int(data.get("timestamp") or 0)
        sessions.append(
            {
                "timestamp": ts,
                "date": _fmt_date(ts) if ts else "",
                "model": str(data.get("model") or "unknown"),
                "task": str(data.get("task") or ""),
                "input_tokens": int(usage.get("input_tokens") or 0),
                "output_tokens": int(usage.get("output_tokens") or 0),
                "total_tokens": int(usage.get("total_tokens") or 0),
                "iterations": int(result.get("iterations") or 0),
                "stop_reason": str(result.get("stop_reason") or ""),
            }
        )
    if not sessions:
        return empty

    sessions.sort(key=lambda s: s["timestamp"], reverse=True)

    day_counts: dict[str, int] = {}
    day_tokens: dict[str, int] = {}
    model_counts: dict[str, int] = {}
    model_tokens: dict[str, int] = {}
    for s in sessions:
        day = s["date"] or "unknown"
        day_counts[day] = day_counts.get(day, 0) + 1
        day_tokens[day] = day_tokens.get(day, 0) + s["total_tokens"]
        model = s["model"]
        model_counts[model] = model_counts.get(model, 0) + 1
        model_tokens[model] = model_tokens.get(model, 0) + s["total_tokens"]

    days_sorted = sorted(day_counts)
    by_model = [
        {"model": m, "sessions": model_counts[m], "total_tokens": model_tokens[m]}
        for m in sorted(model_counts, key=lambda k: -model_tokens[k])
    ]
    recent = [
        {
            "date": s["date"],
            "model": s["model"],
            "task": (
                s["task"][:_TASK_PREVIEW_CHARS] + "…"
                if len(s["task"]) > _TASK_PREVIEW_CHARS
                else s["task"]
            ),
            "total_tokens": s["total_tokens"],
            "iterations": s["iterations"],
            "stop_reason": s["stop_reason"],
        }
        for s in sessions[:_RECENT_SESSIONS]
    ]

    return {
        "source": SOURCE_LIVE,
        "totals": {
            "sessions": len(sessions),
            "input_tokens": sum(s["input_tokens"] for s in sessions),
            "output_tokens": sum(s["output_tokens"] for s in sessions),
            "total_tokens": sum(s["total_tokens"] for s in sessions),
        },
        "by_day": {
            "labels": days_sorted,
            "sessions": [day_counts[d] for d in days_sorted],
            "tokens": [day_tokens[d] for d in days_sorted],
        },
        "by_model": by_model,
        "recent_sessions": recent,
    }


def export_dashboard_json(dest: Path, db_path: Path | None = None, days: int = 30) -> Path:
    """Write a :func:`collect_dashboard_data` snapshot to ``dest`` as JSON."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = collect_dashboard_data(db_path, days=days)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return dest.resolve()
