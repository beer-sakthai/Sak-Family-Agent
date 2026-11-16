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
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from ..config import PERSONA_NAMES, PERSONAS_DIR, eval_log_path, redact_secrets, sakthai_home

logger = logging.getLogger(__name__)

_TASK_PREVIEW_LIMIT = 80

PERSONA_WORKING_FILES: tuple[str, ...] = (
    "SOUL.md",
    "PLAN.md",
    "CYCLE.md",
    "MEMORY.md",
    "HANDOFF.md",
    "BACKPACK.md",
)

_INTRO_PATTERNS = (
    re.compile(r"For me that line is:\s*\n\s*\*\*(.*?)\*\*", re.DOTALL),
    re.compile(r"Every reply I give begins with:\s*\*\*(.*?)\*\*", re.DOTALL),
)


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
    #: Which persona ran this, when the run was scoped to one. Trailing and
    #: defaulted on purpose: the log is append-only, so records written before
    #: this field existed simply lack the key and read back as ``None``. Do not
    #: infer a persona for those — the dashboard shows them as "unattributed".
    persona: str | None = None


def persona_eval_log_path(persona: str) -> Path:
    """Return the sharded eval JSONL path for a persona: ``~/.sakthai/<persona>/eval.jsonl``."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")
    return sakthai_home() / persona / "eval.jsonl"


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


def _collect_records(
    path: Path | None = None,
    persona: str | None = None,
    include_persona_shards: bool = False,
) -> list[dict[str, Any]]:
    """Read eval records, optionally merging sharded per-persona logs and filtering by persona."""
    records = list(_read_records(path))
    if path is None and (include_persona_shards or persona is not None):
        target_personas = (persona,) if persona in PERSONA_NAMES else PERSONA_NAMES
        for p in target_personas:
            for item in _read_records(persona_eval_log_path(p)):
                row = dict(item)
                if not row.get("persona"):
                    row["persona"] = p
                records.append(row)
        records.sort(key=lambda r: int(r.get("timestamp", 0)))

    if persona is not None:
        norm = persona.strip().lower()
        records = [r for r in records if str(r.get("persona") or "").strip().lower() == norm]
    return records


def read_records(path: Path | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    """The parsed eval log, oldest first; the most recent ``limit`` when given.

    Records are plain dicts rather than :class:`EvalRecord`s on purpose: the log
    is append-only and older lines predate fields the dataclass now has, so
    callers read with ``.get()`` and treat a missing key as unknown.
    """
    records = _read_records(path)
    return records[-limit:] if limit is not None else records


def _aggregate_breakdowns(
    records: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    per_model: dict[str, dict[str, Any]] = {}
    per_persona: dict[str, dict[str, Any]] = {}
    for r in records:
        model = str(r.get("model", "unknown"))
        bucket = per_model.setdefault(
            model, {"count": 0, "_latency_total": 0.0, "input_tokens": 0, "output_tokens": 0}
        )
        bucket["count"] += 1
        bucket["_latency_total"] += float(r.get("latency_s", 0.0))
        bucket["input_tokens"] += int(r.get("input_tokens", 0))
        bucket["output_tokens"] += int(r.get("output_tokens", 0))

        raw_persona = r.get("persona")
        p_key = (
            str(raw_persona).strip().lower()
            if isinstance(raw_persona, str) and raw_persona.strip()
            else "unattributed"
        )
        p_bucket = per_persona.setdefault(
            p_key,
            {
                "count": 0,
                "_errors": 0,
                "_latency_total": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            },
        )
        p_bucket["count"] += 1
        if r.get("had_error"):
            p_bucket["_errors"] += 1
        p_bucket["_latency_total"] += float(r.get("latency_s", 0.0))
        p_bucket["input_tokens"] += int(r.get("input_tokens", 0))
        p_bucket["output_tokens"] += int(r.get("output_tokens", 0))

    for bucket in per_model.values():
        bucket["avg_latency_s"] = bucket["_latency_total"] / bucket["count"]
        del bucket["_latency_total"]

    for p_bucket in per_persona.values():
        p_bucket["avg_latency_s"] = p_bucket["_latency_total"] / p_bucket["count"]
        p_bucket["error_rate"] = p_bucket["_errors"] / p_bucket["count"]
        del p_bucket["_latency_total"]
        del p_bucket["_errors"]

    return per_model, per_persona


def summarize_evals(
    path: Path | None = None,
    limit: int = 50,
    persona: str | None = None,
    include_persona_shards: bool = False,
) -> dict[str, Any]:
    """Aggregate recent eval records: latency, tokens, errors, per-model, and per-persona."""
    records = _collect_records(
        path=path, persona=persona, include_persona_shards=include_persona_shards
    )[-limit:]
    if not records:
        return {"count": 0}

    total = len(records)
    errors = sum(1 for r in records if r.get("had_error"))
    total_latency = sum(float(r.get("latency_s", 0.0)) for r in records)
    total_input = sum(int(r.get("input_tokens", 0)) for r in records)
    total_output = sum(int(r.get("output_tokens", 0)) for r in records)
    per_model, per_persona = _aggregate_breakdowns(records)

    return {
        "count": total,
        "error_rate": errors / total,
        "avg_latency_s": total_latency / total,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "per_model": per_model,
        "per_persona": per_persona,
    }


def extract_soul_intro_line(soul_text: str) -> str | None:
    """Extract the mandatory reply intro line from a persona's SOUL.md text."""
    for pattern in _INTRO_PATTERNS:
        match = pattern.search(soul_text)
        if match:
            return match.group(1).strip()
    return None


def _skill_exists(skill_name: str, skills_dir: Path, base_dir: Path) -> bool:
    shared_dir = base_dir / "shared" / "skills"
    library_dir = base_dir.parent / "library"
    return (
        (skills_dir / skill_name / "SKILL.md").is_file()
        or (shared_dir / skill_name / "SKILL.md").is_file()
        or (library_dir / skill_name / "SKILL.md").is_file()
        or any(library_dir.glob(f"*/{skill_name}/SKILL.md"))
    )


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    return loaded if isinstance(loaded, dict) else {}


def evaluate_persona_readiness(persona: str, personas_dir: Path | None = None) -> dict[str, Any]:
    """Evaluate one persona's 6 working files, v9 rubric, config, skills, and evolution."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    base_dir = personas_dir or PERSONAS_DIR
    root = base_dir / persona
    working_files = {name: (root / name).is_file() for name in PERSONA_WORKING_FILES}
    soul_text = (root / "SOUL.md").read_text(encoding="utf-8") if working_files["SOUL.md"] else ""
    cycle_path = root / "CYCLE.md"
    cycle_text = cycle_path.read_text(encoding="utf-8") if working_files["CYCLE.md"] else ""

    cfg_data = _load_yaml_dict(root / "config" / "config.yaml")
    ws_data = _load_yaml_dict(root / "config" / "workspace.yaml")
    raw_model = cfg_data.get("model")
    model_cfg = raw_model if isinstance(raw_model, dict) else {}

    skills_dir = root / "skills"
    skill_count = (
        sum(1 for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
        if skills_dir.is_dir()
        else 0
    )
    primary_skills: list[str] = list(ws_data.get("primary_skills") or [])
    missing_primary = [s for s in primary_skills if not _skill_exists(s, skills_dir, base_dir)]
    intro_line = extract_soul_intro_line(soul_text)
    eval_marker = f"CYCLE EVAL: {persona}"
    evolution_ready = (root / "evolution" / "core" / "fitness.py").is_file()

    return {
        "persona": persona,
        "role": ws_data.get("role"),
        "provider": model_cfg.get("provider"),
        "model": model_cfg.get("default"),
        "working_files": working_files,
        "all_working_files_present": all(working_files.values()),
        "intro_line": intro_line,
        "has_v9_rubric_soul": eval_marker in soul_text,
        "has_v9_rubric_cycle": eval_marker in cycle_text,
        "skill_count": skill_count,
        "primary_skills": primary_skills,
        "missing_primary_skills": missing_primary,
        "primary_skills_present": bool(primary_skills) and not missing_primary,
        "evolution_ready": evolution_ready,
        "ready": (
            all(working_files.values())
            and bool(intro_line)
            and (eval_marker in soul_text)
            and (eval_marker in cycle_text)
            and bool(model_cfg.get("provider"))
            and bool(model_cfg.get("default"))
            and bool(primary_skills)
            and not missing_primary
            and evolution_ready
        ),
    }


def evaluate_all_personas(personas_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Evaluate readiness across all 6 Sak Family personas."""
    return {
        persona: evaluate_persona_readiness(persona, personas_dir=personas_dir)
        for persona in PERSONA_NAMES
    }
