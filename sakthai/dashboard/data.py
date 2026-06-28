"""Dashboard data collection and snapshot export."""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..config import sessions_dir

logger = logging.getLogger(__name__)

SOURCE_LIVE = "live"
SOURCE_DEMO = "demo"
SOURCE_EMPTY = "empty"

_TASK_MAX_LEN = 80

_DAY = 86400
_WEEK = 7 * _DAY
_FACTS_LIMIT = 2000
_OBS_LIMIT = 500

_KIND_COLORS = {
    "pref": "#d9b54a",
    "note": "#c9813f",
    "project": "#3b82f6",
    "profile": "#10b981",
    "skill": "#a855f7",
}
_FALLBACK_COLORS = ["#94a3b8", "#64748b", "#475569", "#334155", "#1e293b"]

DEMO_EVOLUTION: dict[str, Any] = {
    "current_version": "v2.0",
    "performance_gain": "+21%",
    "runs": 12,
    "success_rate": 93.0,
    "neural_focus": [
        {"name": "Context recall", "pct": 91},
        {"name": "Response accuracy", "pct": 93},
        {"name": "Tool selection", "pct": 88},
        {"name": "Knowledge integration", "pct": 85},
        {"name": "Latency reduction", "pct": 82},
    ],
}

DEMO_CHAT: dict[str, Any] = {
    "confidence": 96,
    "messages": [
        {"role": "user", "text": "What is my favorite programming language?"},
        {
            "role": "agent",
            "text": "Based on our past interactions, your favorite programming language is Python.",
        },
    ],
    "thought_process": [
        {
            "group": "Memory retrieval",
            "steps": ["Recall preferences", "Recall recent project context"],
        },
        {
            "group": "Reasoning",
            "steps": ["Rank relevant facts", "Draft grounded answer"],
        },
    ],
}

DEMO_DATA: dict[str, Any] = {
    "generated_at": "demo",
    "source": SOURCE_DEMO,
    "kpis": {
        "total_facts": 5,
        "total_facts_delta": 5,
        "total_observations": 2,
        "total_observations_delta": 2,
        "sessions": 0,
        "total_tokens": 0,
        "total_skills": 0,
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
    "categories": [],
    "evolution": DEMO_EVOLUTION,
    "chat": DEMO_CHAT,
    "skills": [],
    "recent_sessions": [],
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
    except Exception:
        logger.warning("Could not read MemoryStore; using demo data", exc_info=True)
        return dict(DEMO_DATA)

    if not facts and not observations:
        return dict(DEMO_DATA)

    now = int(time.time())
    week_ago = now - _WEEK
    start = now - days * _DAY

    fact_bins = [0] * days
    fact_before_start = 0
    facts_this_week = 0
    counts: dict[str, int] = {}

    for f in facts:
        counts[f.kind] = counts.get(f.kind, 0) + 1
        if f.created_at >= week_ago:
            facts_this_week += 1
        if f.created_at <= start:
            fact_before_start += 1
        else:
            idx = (f.created_at - start - 1) // _DAY
            if 0 <= idx < days:
                fact_bins[idx] += 1

    obs_bins = [0] * days
    obs_before_start = 0
    obs_this_week = 0
    for o in observations:
        if o.created_at >= week_ago:
            obs_this_week += 1
        if o.created_at <= start:
            obs_before_start += 1
        else:
            idx = (o.created_at - start - 1) // _DAY
            if 0 <= idx < days:
                obs_bins[idx] += 1

    labels: list[str] = []
    fact_series: list[int] = []
    obs_series: list[int] = []
    curr_facts = fact_before_start
    curr_obs = obs_before_start
    for d in range(days):
        day_end = start + (d + 1) * _DAY
        labels.append(_fmt_date(day_end - _DAY))
        curr_facts += fact_bins[d]
        curr_obs += obs_bins[d]
        fact_series.append(curr_facts)
        obs_series.append(curr_obs)

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

    session_data = collect_session_data()

    from ..config import LIBRARY_DIR, SKILLS_DIR
    from ..skills import build_catalog

    skills = build_catalog(SKILLS_DIR, LIBRARY_DIR)
    total_skills = (
        sum(int(cat.get("count", 0)) for cat in skills) if isinstance(skills, list) else 0
    )

    return {
        "generated_at": _fmt_date(now),
        "source": SOURCE_LIVE,
        "kpis": {
            "total_facts": len(facts),
            "total_facts_delta": facts_this_week,
            "total_observations": len(observations),
            "total_observations_delta": obs_this_week,
            "sessions": session_data.get("totals", {}).get("sessions", 0),
            "total_tokens": session_data.get("totals", {}).get("total_tokens", 0),
            "total_skills": total_skills,
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
            for f in facts[:10]
        ],
        "top_observations": [
            {"summary": o.summary, "weight": round(o.weight, 2)} for o in observations[:6]
        ],
        "categories": categories,
        "evolution": DEMO_EVOLUTION,
        "chat": DEMO_CHAT,
        "skills": skills,
        "recent_sessions": session_data.get("recent_sessions", []),
    }


def _load_session(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError):
        data = None
    return data if isinstance(data, dict) else None


def collect_session_data(sessions_path: Path | None = None) -> dict[str, Any]:
    _empty: dict[str, Any] = {
        "source": SOURCE_EMPTY,
        "totals": {"sessions": 0, "total_tokens": 0, "input_tokens": 0, "output_tokens": 0},
        "by_model": [],
        "by_day": {"labels": [], "tokens": []},
        "recent_sessions": [],
    }
    base = Path(sessions_path) if sessions_path is not None else sessions_dir()
    if not base.is_dir():
        return _empty

    sessions: list[dict[str, Any]] = []
    total_tokens = 0
    total_input = 0
    total_output = 0
    model_stats: dict[str, dict[str, Any]] = {}
    day_stats: dict[str, int] = {}

    for path in sorted(base.glob("*.json"), reverse=True)[:100]:
        data = _load_session(path)
        if data is None:
            continue
        usage = data.get("usage") or {}
        result = data.get("result") or {}
        ts = int(data.get("timestamp") or 0)
        tokens = int(usage.get("total_tokens") or 0)
        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        total_tokens += tokens
        total_input += input_tokens
        total_output += output_tokens
        model = str(data.get("model") or "unknown")
        if model not in model_stats:
            model_stats[model] = {"model": model, "sessions": 0, "total_tokens": 0}
        model_stats[model]["sessions"] += 1
        model_stats[model]["total_tokens"] += tokens
        if ts:
            day = _fmt_date(ts)
            day_stats[day] = day_stats.get(day, 0) + tokens
        task = str(data.get("task") or "")
        if len(task) > _TASK_MAX_LEN:
            task = task[:_TASK_MAX_LEN] + "…"
        sessions.append(
            {
                "date": _fmt_date(ts) if ts else "",
                "model": model,
                "task": task,
                "total_tokens": tokens,
                "iterations": int(result.get("iterations") or 0),
                "stop_reason": str(result.get("stop_reason") or ""),
            }
        )

    if not sessions:
        return _empty

    sorted_days = sorted(day_stats.keys())
    return {
        "source": SOURCE_LIVE,
        "totals": {
            "sessions": len(sessions),
            "total_tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
        },
        "by_model": sorted(model_stats.values(), key=lambda m: -int(m["total_tokens"])),
        "by_day": {"labels": sorted_days, "tokens": [day_stats[d] for d in sorted_days]},
        "recent_sessions": sessions[:20],
    }


def export_dashboard_json(dest: Path, db_path: Path | None = None, days: int = 30) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = collect_dashboard_data(db_path, days=days)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return dest.resolve()
