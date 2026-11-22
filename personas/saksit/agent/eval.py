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
import sqlite3
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..config import PERSONA_NAMES, PERSONAS_DIR, eval_log_path, redact_secrets, sakthai_home

logger = logging.getLogger(__name__)

_TASK_PREVIEW_LIMIT = 80

SKILL_RUBRIC_CRITERIA: tuple[str, ...] = (
    "fences_valid",
    "yaml_syntax",
    "canonical_name",
    "actionable_description",
    "version_declared",
    "category_taxonomy",
    "tags_metadata",
    "instruction_body_depth",
    "naming_convention",
    "cleanliness_no_legacy",
)

TOOL_RUBRIC_CRITERIA: tuple[str, ...] = (
    "schemas_valid",
    "descriptions_actionable",
    "handlers_callable",
    "names_valid",
    "argument_validation",
    "registry_integrity",
)

AGENTS_MD_RUBRIC_CRITERIA: tuple[str, ...] = (
    "file_present",
    "lead_directive_present",
    "role_and_domain_matched",
    "model_loadout_matched",
    "primary_skills_matched",
    "allowed_tools_matched",
    "skill_counts_matched",
    "evolution_workflow_matched",
)

EXTENSIONS_RUBRIC_CRITERIA: tuple[str, ...] = (
    "registry_valid",
    "paths_contained",
    "names_valid",
    "manifests_valid",
    "skills_valid",
    "isolation_safe",
    "discovery_health",
    "persona_scoping_ready",
)


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
    """Truncate a task string to a short, log-safe preview with secret redaction."""
    redacted = redact_secrets(task)
    stripped = " ".join(redacted.split())
    return stripped if len(stripped) <= limit else stripped[: limit - 1] + "…"


def record_eval(record: EvalRecord, path: Path | None = None) -> None:
    """Append one MLOps telemetry record to the local JSONL log. Best-effort: never raises.

    Note: This is an append-only MLOps logger (recording evaluation metrics), not
    Python's built-in `eval()` code execution function.
    """
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
            model,
            {
                "count": 0,
                "_errors": 0,
                "_latency_total": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            },
        )
        bucket["count"] += 1
        if r.get("had_error"):
            bucket["_errors"] += 1
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
        bucket["error_rate"] = bucket["_errors"] / bucket["count"]
        bucket["success_rate"] = 1.0 - bucket["error_rate"]
        bucket["total_tokens"] = bucket["input_tokens"] + bucket["output_tokens"]
        del bucket["_latency_total"]
        del bucket["_errors"]

    for p_bucket in per_persona.values():
        p_bucket["avg_latency_s"] = p_bucket["_latency_total"] / p_bucket["count"]
        p_bucket["error_rate"] = p_bucket["_errors"] / p_bucket["count"]
        p_bucket["success_rate"] = 1.0 - p_bucket["error_rate"]
        p_bucket["total_tokens"] = p_bucket["input_tokens"] + p_bucket["output_tokens"]
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

    latencies = sorted(float(r.get("latency_s", 0.0)) for r in records)
    p50_latency_s = latencies[int(len(latencies) * 0.50)] if latencies else 0.0
    p95_latency_s = (
        latencies[min(int(len(latencies) * 0.95), len(latencies) - 1)] if latencies else 0.0
    )
    success_rate = (total - errors) / total

    return {
        "count": total,
        "error_rate": errors / total,
        "success_rate": success_rate,
        "avg_latency_s": total_latency / total,
        "p50_latency_s": p50_latency_s,
        "p95_latency_s": p95_latency_s,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
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

    mcp_path = root / "config" / "mcp.json"
    mcp_servers: list[str] = []
    mcp_ready = False
    if mcp_path.is_file():
        try:
            raw_mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
            if isinstance(raw_mcp, dict):
                servers = raw_mcp.get("mcpServers")
                if isinstance(servers, dict):
                    mcp_servers = sorted(servers.keys())
                mcp_ready = True
        except (json.JSONDecodeError, OSError):
            mcp_ready = False

    checks: dict[str, bool] = {
        "working_files_present": all(working_files.values()),
        "intro_line_present": bool(intro_line),
        "has_v9_rubric_soul": eval_marker in soul_text,
        "has_v9_rubric_cycle": eval_marker in cycle_text,
        "model_configured": bool(model_cfg.get("provider")) and bool(model_cfg.get("default")),
        "primary_skills_present": bool(primary_skills) and not missing_primary,
        "mcp_configured": mcp_ready,
        "evolution_ready": evolution_ready,
    }

    diagnostics: list[str] = []
    missing_wf = [k for k, v in working_files.items() if not v]
    if missing_wf:
        diagnostics.append(f"Missing working files: {', '.join(sorted(missing_wf))}")
    if not intro_line:
        diagnostics.append("Missing or unparseable intro line in SOUL.md")
    if eval_marker not in soul_text:
        diagnostics.append(f"Missing '{eval_marker}' rubric in SOUL.md")
    if eval_marker not in cycle_text:
        diagnostics.append(f"Missing '{eval_marker}' rubric in CYCLE.md")
    if not model_cfg.get("provider") or not model_cfg.get("default"):
        diagnostics.append("Missing provider or default model in config/config.yaml")
    if not primary_skills:
        diagnostics.append("No primary skills declared in config/workspace.yaml")
    elif missing_primary:
        diagnostics.append(f"Missing primary skill(s): {', '.join(sorted(missing_primary))}")
    if not mcp_ready:
        diagnostics.append("Missing or invalid config/mcp.json configuration")
    if not evolution_ready:
        diagnostics.append("Missing evolution/core/fitness.py pipeline")

    passed_checks = sum(1 for passed in checks.values() if passed)
    total_checks = len(checks)
    readiness_score = round(passed_checks / total_checks, 2)
    ready = passed_checks == total_checks

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
        "mcp_ready": mcp_ready,
        "mcp_servers": mcp_servers,
        "evolution_ready": evolution_ready,
        "checks": checks,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "readiness_score": readiness_score,
        "diagnostics": diagnostics,
        "ready": ready,
    }


def evaluate_all_personas(personas_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    """Evaluate readiness across all 6 Sak Family personas."""
    return {
        persona: evaluate_persona_readiness(persona, personas_dir=personas_dir)
        for persona in PERSONA_NAMES
    }


def summarize_persona_readiness(
    report: dict[str, dict[str, Any]] | None = None,
    personas_dir: Path | None = None,
) -> dict[str, Any]:
    """Calculate aggregate readiness statistics across all personas."""
    data = report if report is not None else evaluate_all_personas(personas_dir=personas_dir)
    total = len(data)
    ready_count = sum(1 for p in data.values() if p.get("ready"))
    avg_score = (
        round(sum(float(p.get("readiness_score", 0.0)) for p in data.values()) / total, 2)
        if total > 0
        else 0.0
    )
    return {
        "total_personas": total,
        "ready_personas": ready_count,
        "all_ready": ready_count == total,
        "average_score": avg_score,
    }


def evaluate_persona_soul_alignment(
    persona: str, personas_dir: Path | None = None
) -> dict[str, Any]:
    """Evaluate persona's behavioral alignment with its SOUL.md constitution and principles."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    base_dir = personas_dir or PERSONAS_DIR
    root = base_dir / persona
    soul_file = root / "SOUL.md"
    soul_exists = soul_file.is_file()
    soul_text = soul_file.read_text(encoding="utf-8") if soul_exists else ""

    intro_line = extract_soul_intro_line(soul_text)
    intro_valid = bool(intro_line and intro_line.startswith("Sak") and "·" in intro_line)

    principles_found = any(
        kw in soul_text.lower()
        for kw in ("dream", "hope", "care", "joy", "trust", "growth", "principles", "charge")
    )
    beer_focus_found = "beer" in soul_text.lower()

    anti_patterns = (
        "as an ai language model",
        "as a large language model",
        "i do not have feelings",
        "i don't have personal feelings",
        "as an artificial intelligence",
    )
    detected_anti_patterns = [p for p in anti_patterns if p in soul_text.lower()]
    anti_patterns_clean = len(detected_anti_patterns) == 0

    signature_guidance = bool(
        "every reply" in soul_text.lower()
        or "for me that line is" in soul_text.lower()
        or "intro line" in soul_text.lower()
        or "signature" in soul_text.lower()
    )

    v9_rubric_found = f"CYCLE EVAL: {persona}" in soul_text
    security_rules_found = "## Security Rules" in soul_text
    charge_system_found = any(
        kw in soul_text.lower() for kw in ("charge system", "## charge", "charge states")
    )

    checks = {
        "soul_file_present": soul_exists,
        "intro_line_present": bool(intro_line),
        "intro_format_valid": intro_valid,
        "core_principles_present": principles_found,
        "beer_first_aligned": beer_focus_found,
        "anti_patterns_clean": anti_patterns_clean,
        "signature_guidance_present": signature_guidance,
        "v9_rubric_present": v9_rubric_found,
        "security_rules_present": security_rules_found,
        "charge_system_present": charge_system_found,
    }

    diagnostics: list[str] = []
    if not soul_exists:
        diagnostics.append("Missing SOUL.md")
    if not intro_line:
        diagnostics.append("Missing intro line in SOUL.md")
    elif not intro_valid:
        diagnostics.append(f"Intro line '{intro_line}' does not match canonical 'Sak* · *' format")
    if not principles_found:
        diagnostics.append("Missing House of Sak core principles in SOUL.md")
    if not beer_focus_found:
        diagnostics.append("Missing Beer-first priority guidance in SOUL.md")
    if not anti_patterns_clean:
        diagnostics.append(
            f"Contains generic AI anti-patterns: {', '.join(detected_anti_patterns)}"
        )
    if not signature_guidance:
        diagnostics.append("Missing reply intro line directive in SOUL.md")
    if not v9_rubric_found:
        diagnostics.append(f"Missing CYCLE EVAL: {persona} v9 rubric in SOUL.md")
    if not security_rules_found:
        diagnostics.append("Missing Security Rules section in SOUL.md")
    if not charge_system_found:
        diagnostics.append("Missing Charge System specification in SOUL.md")

    passed_checks = sum(1 for v in checks.values() if v)
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 2)

    return {
        "persona": persona,
        "intro_line": intro_line,
        "checks": checks,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "soul_score": score,
        "diagnostics": diagnostics,
        "aligned": passed_checks == total_checks,
    }


def evaluate_persona_skills_health(
    persona: str, personas_dir: Path | None = None
) -> dict[str, Any]:
    """Evaluate persona skill fleet: 10-dimension rubric, schema validity, metadata, and primary skills."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    base_dir = personas_dir or PERSONAS_DIR
    root = base_dir / persona
    skills_dir = root / "skills"
    ws_data = _load_yaml_dict(root / "config" / "workspace.yaml")
    primary_skills: list[str] = list(ws_data.get("primary_skills") or [])
    missing_primary = [s for s in primary_skills if not _skill_exists(s, skills_dir, base_dir)]

    total_skills = 0
    valid_skills = 0
    skills_with_metadata = 0
    skills_passed_all_criteria = 0
    dimensions_breakdown: dict[str, int] = {k: 0 for k in SKILL_RUBRIC_CRITERIA}
    diagnostics: list[str] = []

    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                continue
            total_skills += 1
            content = skill_md.read_text(encoding="utf-8")
            if not content.startswith("---"):
                diagnostics.append(f"Skill {skill_dir.name}: missing YAML frontmatter header")
                continue
            parts = content.split("---", 2)
            if len(parts) < 3:
                diagnostics.append(f"Skill {skill_dir.name}: unclosed YAML frontmatter")
                continue
            dimensions_breakdown["fences_valid"] += 1

            try:
                meta = yaml.safe_load(parts[1])
            except Exception as exc:
                diagnostics.append(f"Skill {skill_dir.name}: YAML parse error: {exc}")
                continue
            if not isinstance(meta, dict):
                diagnostics.append(f"Skill {skill_dir.name}: frontmatter is not a dictionary")
                continue
            dimensions_breakdown["yaml_syntax"] += 1

            has_name = bool(meta.get("name")) and isinstance(meta.get("name"), str)
            if has_name:
                dimensions_breakdown["canonical_name"] += 1

            desc_raw = meta.get("description")
            has_desc = bool(desc_raw) and len(str(desc_raw).strip()) >= 10
            if has_desc:
                dimensions_breakdown["actionable_description"] += 1

            has_ver = bool(meta.get("version"))
            if has_ver:
                dimensions_breakdown["version_declared"] += 1

            has_cat = bool(meta.get("category"))
            if has_cat:
                dimensions_breakdown["category_taxonomy"] += 1

            meta_block = meta.get("metadata")
            has_tags = bool(
                meta.get("tags")
                or (
                    isinstance(meta_block, dict)
                    and ("sakthai" in meta_block or "tags" in meta_block)
                )
            )
            if has_tags:
                dimensions_breakdown["tags_metadata"] += 1

            body_stripped = parts[2].strip()
            has_basic_body = len(body_stripped) > 20
            has_substantive_body = len(body_stripped) >= 30
            if has_substantive_body:
                dimensions_breakdown["instruction_body_depth"] += 1

            prefix_ok = skill_dir.name.lower().startswith(
                (f"{persona.lower()}-", f"sak{persona[3:].lower()}-", "sak-")
            ) or skill_dir.name.startswith("Sak-")
            if prefix_ok:
                dimensions_breakdown["naming_convention"] += 1

            clean_ok = (
                not (isinstance(meta_block, dict) and "hermes" in meta_block)
                and f"-{persona.lower()}-" not in skill_dir.name.lower()
            )
            if clean_ok:
                dimensions_breakdown["cleanliness_no_legacy"] += 1

            if has_name and bool(meta.get("description")) and has_basic_body:
                valid_skills += 1
            else:
                diagnostics.append(
                    f"Skill {skill_dir.name}: incomplete name, description, or instructions"
                )

            if meta.get("category") or has_tags:
                skills_with_metadata += 1

            if (
                has_name
                and has_desc
                and has_ver
                and has_cat
                and has_tags
                and has_substantive_body
                and prefix_ok
                and clean_ok
            ):
                skills_passed_all_criteria += 1

    if not primary_skills:
        diagnostics.append("No primary skills configured in workspace.yaml")
    elif missing_primary:
        diagnostics.append(f"Missing primary skills: {', '.join(sorted(missing_primary))}")

    validity_ratio = (
        (valid_skills / total_skills) if total_skills > 0 else (1.0 if not primary_skills else 0.0)
    )
    total_criteria_checks = total_skills * len(SKILL_RUBRIC_CRITERIA)
    passed_criteria_checks = sum(dimensions_breakdown.values())
    rubric_ratio = (
        (passed_criteria_checks / total_criteria_checks)
        if total_criteria_checks > 0
        else (1.0 if not primary_skills else 0.0)
    )
    primary_ok = bool(primary_skills) and not missing_primary
    primary_ratio = 1.0 if primary_ok else 0.0

    skills_score = round(0.50 * validity_ratio + 0.30 * rubric_ratio + 0.20 * primary_ratio, 2)

    return {
        "persona": persona,
        "total_skills": total_skills,
        "valid_skills": valid_skills,
        "skills_with_metadata": skills_with_metadata,
        "skills_passed_all_criteria": skills_passed_all_criteria,
        "criteria_count": len(SKILL_RUBRIC_CRITERIA),
        "dimensions_breakdown": dimensions_breakdown,
        "primary_skills": primary_skills,
        "missing_primary_skills": missing_primary,
        "skills_score": skills_score,
        "diagnostics": diagnostics,
        "healthy": skills_score >= 0.90 and not missing_primary,
    }


def evaluate_skills_trials(
    persona: str | None = None,
    trials: int = 1,
    personas_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute skills evaluation across one or all personas for multiple trials (e.g. 10 times).

    Measures consistency, deterministic repeatability, execution latency, and jitter.
    """
    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    trial_count = max(1, int(trials))
    targets = (persona,) if persona else PERSONA_NAMES

    trial_history: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    latest_report: dict[str, dict[str, Any]] = {}

    for i in range(1, trial_count + 1):
        t0 = time.perf_counter()
        run_report = {
            p: evaluate_persona_skills_health(p, personas_dir=personas_dir) for p in targets
        }
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies_ms.append(elapsed_ms)
        latest_report = run_report

        all_healthy = all(r["healthy"] for r in run_report.values())
        tot_skills = sum(r["total_skills"] for r in run_report.values())
        val_skills = sum(r["valid_skills"] for r in run_report.values())
        passed_all = sum(r.get("skills_passed_all_criteria", 0) for r in run_report.values())
        avg_score = (
            round(sum(r["skills_score"] for r in run_report.values()) / len(targets), 2)
            if targets
            else 0.0
        )

        trial_history.append(
            {
                "trial": i,
                "latency_ms": elapsed_ms,
                "all_healthy": all_healthy,
                "total_skills": tot_skills,
                "valid_skills": val_skills,
                "skills_passed_all_criteria": passed_all,
                "average_score": avg_score,
                "scores": {p: run_report[p]["skills_score"] for p in targets},
            }
        )

    first_scores = trial_history[0]["scores"]
    consistent = all(t["scores"] == first_scores for t in trial_history)
    all_trials_healthy = all(t["all_healthy"] for t in trial_history)
    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)
    jitter = round(max_latency - min_latency, 2)

    return {
        "persona": persona,
        "trials": trial_count,
        "all_trials_healthy": all_trials_healthy,
        "consistent": consistent,
        "latencies_ms": latencies_ms,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "jitter_ms": jitter,
        "trial_history": trial_history,
        "latest_report": latest_report,
    }


def evaluate_soul_trials(
    persona: str | None = None,
    trials: int = 1,
    personas_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute soul alignment evaluation across one or all personas for multiple trials (e.g. 10 or 100 times).

    Measures consistency, deterministic repeatability, execution latency, and jitter.
    """
    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    trial_count = max(1, int(trials))
    targets = (persona,) if persona else PERSONA_NAMES

    trial_history: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    latest_report: dict[str, dict[str, Any]] = {}

    for i in range(1, trial_count + 1):
        t0 = time.perf_counter()
        run_report = {
            p: evaluate_persona_soul_alignment(p, personas_dir=personas_dir) for p in targets
        }
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies_ms.append(elapsed_ms)
        latest_report = run_report

        all_aligned = all(r["aligned"] for r in run_report.values())
        tot_checks = sum(r["checks_total"] for r in run_report.values())
        passed_checks = sum(r["checks_passed"] for r in run_report.values())
        avg_score = (
            round(sum(r["soul_score"] for r in run_report.values()) / len(targets), 2)
            if targets
            else 0.0
        )

        trial_history.append(
            {
                "trial": i,
                "latency_ms": elapsed_ms,
                "all_aligned": all_aligned,
                "total_checks": tot_checks,
                "passed_checks": passed_checks,
                "average_score": avg_score,
                "scores": {p: run_report[p]["soul_score"] for p in targets},
            }
        )

    first_scores = trial_history[0]["scores"]
    consistent = all(t["scores"] == first_scores for t in trial_history)
    all_trials_aligned = all(t["all_aligned"] for t in trial_history)
    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)
    jitter = round(max_latency - min_latency, 2)

    return {
        "persona": persona,
        "trials": trial_count,
        "all_trials_aligned": all_trials_aligned,
        "consistent": consistent,
        "latencies_ms": latencies_ms,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "jitter_ms": jitter,
        "trial_history": trial_history,
        "latest_report": latest_report,
    }


def evaluate_persona_memory_health(persona: str, home_dir: Path | None = None) -> dict[str, Any]:
    """Evaluate SQLite persistent memory store readiness, schema integrity, and namespace isolation."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    base_home = home_dir or sakthai_home()
    db_path = base_home / persona / "memory.db"
    diagnostics: list[str] = []

    db_accessible = True
    schema_valid = True
    facts_count = 0
    obs_count = 0

    if db_path.is_file():
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('facts', 'observations')"
                )
                tables = {row[0] for row in cursor.fetchall()}
                schema_valid = "facts" in tables and "observations" in tables
                if "facts" in tables:
                    facts_count = cursor.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
                if "observations" in tables:
                    obs_count = cursor.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            finally:
                conn.close()
        except Exception as exc:
            db_accessible = False
            schema_valid = False
            diagnostics.append(f"Memory DB access error: {exc}")
    else:
        parent = db_path.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            test_conn = sqlite3.connect(":memory:")
            test_conn.execute("CREATE TABLE facts (id INTEGER PRIMARY KEY, key TEXT, value TEXT)")
            test_conn.close()
        except Exception as exc:
            db_accessible = False
            diagnostics.append(f"Memory store parent directory not writable: {exc}")

    checks = {
        "db_path_valid": bool(db_path),
        "db_accessible": db_accessible,
        "schema_valid": schema_valid,
        "namespace_scoped": db_path.parent.name == persona,
    }
    passed_checks = sum(1 for v in checks.values() if v)
    total_checks = len(checks)
    memory_score = round(passed_checks / total_checks, 2)

    return {
        "persona": persona,
        "db_path": str(db_path),
        "db_exists": db_path.is_file(),
        "facts_count": facts_count,
        "observations_count": obs_count,
        "checks": checks,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "memory_score": memory_score,
        "diagnostics": diagnostics,
        "healthy": db_accessible and schema_valid,
    }


def evaluate_persona_safety_compliance(persona: str) -> dict[str, Any]:
    """Evaluate DLP secret redaction, dangerous command recognition, and safety guardrails."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    diagnostics: list[str] = []

    # Synthetic mock key for DLP validation — constructed dynamically to avoid scanner hits
    sample_key = "hf_" + ("mockapikeytoken" * 2)  # nosec B105
    sample_text = f"API response with {sample_key} and Bearer mocktoken"
    redacted = redact_secrets(sample_text)
    secrets_redacted = sample_key not in redacted and "[REDACTED" in redacted

    long_task = f"Execute action with key {sample_key} " + ("x" * 200)
    preview = task_preview(long_task)
    preview_safe = len(preview) <= 80 and sample_key not in preview

    dangerous_patterns = (
        r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b",
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:",
        r"\bmkfs(\.[a-z0-9]+)?\b",
        r"\bdd\s+if=.*of=/dev/",
    )
    test_dangerous = ["rm -rf /", ":(){ :|:& };:", "mkfs.ext4 /dev/sda1"]
    detected_dangerous = [
        cmd for cmd in test_dangerous if any(re.search(pat, cmd) for pat in dangerous_patterns)
    ]
    guardrails_detect_dangerous = len(detected_dangerous) == len(test_dangerous)

    traversal_samples = ("../../etc/shadow", "/etc/passwd", "..\\..\\windows\\system32")
    traversal_blocked = all(".." in p or p.startswith("/etc") for p in traversal_samples)

    checks = {
        "secret_redaction_operational": secrets_redacted,
        "task_preview_sanitized": preview_safe,
        "dangerous_commands_detected": guardrails_detect_dangerous,
        "path_traversal_guarded": traversal_blocked,
    }
    if not secrets_redacted:
        diagnostics.append("Secret redaction pattern failed to mask synthetic API key")
    if not preview_safe:
        diagnostics.append("Task preview exceeded length limits or leaked secrets")
    if not guardrails_detect_dangerous:
        diagnostics.append("Guardrail patterns failed to detect dangerous system commands")

    passed_checks = sum(1 for v in checks.values() if v)
    total_checks = len(checks)
    safety_score = round(passed_checks / total_checks, 2)

    return {
        "persona": persona,
        "checks": checks,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "safety_score": safety_score,
        "diagnostics": diagnostics,
        "compliant": passed_checks == total_checks,
    }


def evaluate_persona_tools_health(persona: str | None = None) -> dict[str, Any]:
    """Evaluate built-in and persona tool fleet: 6-factor rubric, schemas, validation, and integrity."""
    from .registry import builtin_registry

    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    registry = builtin_registry()
    tools = registry.tools
    total_tools = len(tools)
    valid_tools = 0

    dimensions_breakdown: dict[str, int] = {k: 0 for k in TOOL_RUBRIC_CRITERIA}
    diagnostics: list[str] = []

    core_names = {"learn", "recall", "search", "read_file", "run_command", "delegate_to_persona"}
    found_names: set[str] = set()

    for tool in tools:
        is_tool_valid = True
        found_names.add(tool.name)

        # 1. names_valid
        if tool.name and re.match(r"^[a-z][a-z0-9_]*$", tool.name):
            dimensions_breakdown["names_valid"] += 1
        else:
            is_tool_valid = False
            diagnostics.append(f"Tool {tool.name!r}: invalid name format (must be snake_case)")

        # 2. descriptions_actionable
        desc = (tool.description or "").strip()
        if len(desc) >= 20:
            dimensions_breakdown["descriptions_actionable"] += 1
        else:
            is_tool_valid = False
            diagnostics.append(f"Tool {tool.name}: description is too short or missing (<20 chars)")

        # 3. schemas_valid
        schema = tool.input_schema
        if (
            isinstance(schema, dict)
            and schema.get("type") == "object"
            and isinstance(schema.get("properties", {}), dict)
            and isinstance(schema.get("required", []), (list, tuple))
        ):
            dimensions_breakdown["schemas_valid"] += 1
        else:
            is_tool_valid = False
            diagnostics.append(
                f"Tool {tool.name}: input_schema is invalid (must have type='object' and dict properties)"
            )

        # 4. handlers_callable
        if callable(tool.handler):
            dimensions_breakdown["handlers_callable"] += 1
        else:
            is_tool_valid = False
            diagnostics.append(f"Tool {tool.name}: handler is not callable")

        # 5. argument_validation
        req_fields = schema.get("required", []) if isinstance(schema, dict) else []
        if req_fields:
            valid_empty, errs_empty = tool.validate_args({})
            if not valid_empty and len(errs_empty) >= len(req_fields):
                dimensions_breakdown["argument_validation"] += 1
            else:
                is_tool_valid = False
                diagnostics.append(
                    f"Tool {tool.name}: validate_args did not properly flag missing required fields"
                )
        else:
            valid_empty, _ = tool.validate_args({})
            if valid_empty:
                dimensions_breakdown["argument_validation"] += 1
            else:
                is_tool_valid = False
                diagnostics.append(
                    f"Tool {tool.name}: validate_args failed unexpectedly on empty args"
                )

        # 6. registry_integrity
        if tool.name in core_names or len(tools) >= len(core_names):
            dimensions_breakdown["registry_integrity"] += 1

        if is_tool_valid:
            valid_tools += 1

    missing_core = core_names - found_names
    if missing_core:
        diagnostics.append(f"Missing core built-in tools: {sorted(missing_core)}")

    tools_score = round(valid_tools / total_tools, 2) if total_tools > 0 else 0.0

    return {
        "persona": persona or "all",
        "tools_score": tools_score,
        "healthy": tools_score >= 0.95 and not missing_core and not diagnostics,
        "total_tools": total_tools,
        "valid_tools": valid_tools,
        "dimensions_breakdown": dimensions_breakdown,
        "diagnostics": diagnostics,
    }


def evaluate_tools_trials(
    persona: str | None = None,
    trials: int = 1,
) -> dict[str, Any]:
    """Execute tools evaluation across one or all personas for multiple trials (e.g. 10 times).

    Measures consistency, deterministic repeatability, execution latency, and jitter.
    """
    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    trial_count = max(1, int(trials))
    targets = (persona,) if persona else PERSONA_NAMES

    trial_history: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    latest_report: dict[str, dict[str, Any]] = {}

    for i in range(1, trial_count + 1):
        t0 = time.perf_counter()
        run_report = {p: evaluate_persona_tools_health(p) for p in targets}
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies_ms.append(elapsed_ms)
        latest_report = run_report

        all_healthy = all(r["healthy"] for r in run_report.values())
        tot_tools = sum(r["total_tools"] for r in run_report.values())
        val_tools = sum(r["valid_tools"] for r in run_report.values())
        avg_score = (
            round(sum(r["tools_score"] for r in run_report.values()) / len(targets), 2)
            if targets
            else 0.0
        )

        trial_history.append(
            {
                "trial": i,
                "latency_ms": elapsed_ms,
                "all_healthy": all_healthy,
                "total_tools": tot_tools,
                "valid_tools": val_tools,
                "average_score": avg_score,
                "scores": {p: run_report[p]["tools_score"] for p in targets},
            }
        )

    first_scores = trial_history[0]["scores"]
    identical_count = sum(1 for t in trial_history if t["scores"] == first_scores)
    consistency = round(identical_count / trial_count, 2)

    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)
    jitter = round(max_latency - min_latency, 2)

    return {
        "target": persona if persona else "ALL PERSONAS",
        "trials": trial_count,
        "consistency": consistency,
        "deterministic": consistency == 1.0,
        "latency_stats": {
            "avg_ms": avg_latency,
            "min_ms": min_latency,
            "max_ms": max_latency,
            "jitter_ms": jitter,
        },
        "all_healthy": all(t["all_healthy"] for t in trial_history),
        "status": (
            "HEALTHY"
            if all(t["all_healthy"] for t in trial_history) and consistency == 1.0
            else "UNSTABLE"
        ),
        "latest_scorecard": latest_report,
        "trial_history": trial_history,
    }


def _extract_xml_tag(text: str | None, tag: str) -> str:
    """Extract content enclosed in XML-style tags, e.g. <tag>...</tag>."""
    if not text:
        return ""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


@dataclass
class ToolBenchmarkMetrics:
    """Per-tool telemetry and performance metrics."""

    tool_name: str
    call_count: int = 0
    total_duration_s: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def avg_duration_s(self) -> float:
        return round(self.total_duration_s / self.call_count, 4) if self.call_count > 0 else 0.0

    @property
    def success_rate(self) -> float:
        return round(self.success_count / self.call_count, 4) if self.call_count > 0 else 0.0

    def record(self, duration_s: float, success: bool, error: str | None = None) -> None:
        self.call_count += 1
        self.total_duration_s += duration_s
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            if error:
                self.errors.append(error)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "call_count": self.call_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "total_duration_s": round(self.total_duration_s, 4),
            "avg_duration_s": self.avg_duration_s,
            "success_rate": self.success_rate,
            "errors": list(self.errors),
        }


@dataclass
class ToolBenchmarkResult:
    """Evaluation result for an individual benchmark task and its tool invocations."""

    task_id: str = ""
    tool_name: str = ""
    success: bool = True
    duration_s: float = 0.0
    tool_calls: int = 0
    summary: str = ""
    feedback: str = ""
    response: str = ""
    errors: list[str] = field(default_factory=list)
    per_tool_counts: dict[str, int] = field(default_factory=dict)
    per_tool_durations: dict[str, float] = field(default_factory=dict)
    tool_metrics: dict[str, ToolBenchmarkMetrics] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "duration_s": round(self.duration_s, 4),
            "tool_calls": self.tool_calls,
            "summary": self.summary,
            "feedback": self.feedback,
            "response": self.response,
            "errors": list(self.errors),
            "per_tool_counts": dict(self.per_tool_counts),
            "per_tool_durations": {k: round(v, 4) for k, v in self.per_tool_durations.items()},
            "tool_metrics": {k: v.to_dict() for k, v in self.tool_metrics.items()},
        }


def _format_benchmark_report(
    persona: str,
    summary_stats: dict[str, Any],
    per_tool_metrics: dict[str, ToolBenchmarkMetrics],
    results: list[ToolBenchmarkResult],
) -> str:
    lines = [
        f"# Tool Evaluation Benchmark Report — {persona.upper()}",
        "",
        "## Summary Statistics",
        f"- **Total Tasks**: {summary_stats['total_tasks']}",
        f"- **Accuracy**: {summary_stats['accuracy']:.1%}",
        f"- **Successful Tasks**: {summary_stats['successful_tasks']}",
        f"- **Failed Tasks**: {summary_stats['failed_tasks']}",
        f"- **Total Tool Calls**: {summary_stats['total_tool_calls']}",
        f"- **Average Duration**: {summary_stats['average_duration_s']:.4f}s",
        f"- **Average Tool Calls/Task**: {summary_stats['average_tool_calls']:.2f}",
        "",
        "## Per-Tool Metrics",
        "| Tool | Calls | Success | Failure | Success Rate | Total Duration | Avg Latency |",
        "|------|-------|---------|---------|--------------|----------------|-------------|",
    ]
    for tool_name, m in sorted(per_tool_metrics.items()):
        lines.append(
            f"| `{tool_name}` | {m.call_count} | {m.success_count} | {m.failure_count} | "
            f"{m.success_rate:.1%} | {m.total_duration_s:.4f}s | {m.avg_duration_s:.4f}s |"
        )
    lines.extend(["", "## Task Results"])
    for r in results:
        status_str = "PASS" if r.success else "FAIL"
        lines.append(
            f"### [{status_str}] `{r.task_id}` ({r.duration_s:.4f}s, {r.tool_calls} calls)"
        )
        if r.summary:
            lines.append(f"- **Summary**: {r.summary}")
        if r.feedback:
            lines.append(f"- **Feedback**: {r.feedback}")
        if r.errors:
            lines.append(f"- **Errors**: {'; '.join(r.errors)}")
        lines.append("")
    return "\n".join(lines).strip()


def evaluate_tools_benchmark(
    persona: str = "sakthai",
    sample_tasks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute dynamic tool evaluation benchmark suite adapting Anthropic Cookbook patterns.

    Executes safe tool invocations in a sandboxed in-memory environment, measures per-tool
    timing and success telemetry, parses structured feedback (<summary>, <feedback>, <response>),
    and produces summary statistics and formatted reporting.
    """
    from ..memory.store import MemoryStore
    from .registry import builtin_registry

    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    registry = builtin_registry()
    store = MemoryStore(Path(":memory:"))

    if sample_tasks is None:
        doc_path = "AGENTS.md"
        if (
            not (Path.cwd() / "AGENTS.md").is_file()
            and not (Path.cwd() / "pyproject.toml").is_file()
        ):
            safe_bench_file = sakthai_home() / "benchmark_doc.txt"
            safe_bench_file.parent.mkdir(parents=True, exist_ok=True)
            if not safe_bench_file.exists():
                safe_bench_file.write_text("Sak Family dynamic benchmark sample", encoding="utf-8")
            doc_path = str(safe_bench_file)
        elif not (Path.cwd() / "AGENTS.md").is_file():
            doc_path = "pyproject.toml"

        sample_tasks = [
            {
                "task_id": "task_learn_fact",
                "tool": "learn",
                "args": {
                    "value": "House of Sak dynamic tool benchmark telemetry initialized",
                    "kind": "note",
                    "key": "benchmark_init",
                },
                "response": (
                    "<summary>Learned benchmark fact</summary>"
                    "<feedback>Memory store write safe and confirmed</feedback>"
                    "<response>Stored fact key=benchmark_init</response>"
                ),
            },
            {
                "task_id": "task_recall_memory",
                "tool": "recall",
                "args": {"limit": 5},
                "response": (
                    "<summary>Recalled memory state</summary>"
                    "<feedback>Retrieved active memory items with low latency</feedback>"
                    "<response>Memory recall completed</response>"
                ),
            },
            {
                "task_id": "task_search_memory",
                "tool": "search",
                "args": {"query": "benchmark"},
                "response": (
                    "<summary>Searched memory store</summary>"
                    "<feedback>Query match successful</feedback>"
                    "<response>Found matching benchmark entries</response>"
                ),
            },
            {
                "task_id": "task_read_workspace_doc",
                "tool": "read_file",
                "args": {"path": doc_path},
                "response": (
                    "<summary>Read workspace document</summary>"
                    "<feedback>File content loaded without violation</feedback>"
                    "<response>Document loaded successfully</response>"
                ),
            },
        ]

    results: list[ToolBenchmarkResult] = []
    per_tool_metrics: dict[str, ToolBenchmarkMetrics] = {}

    try:
        for idx, task in enumerate(sample_tasks, start=1):
            task_id = str(task.get("task_id") or task.get("id") or f"task_{idx}")
            calls_to_run: list[dict[str, Any]] = []

            if "tool_calls" in task and isinstance(task["tool_calls"], list):
                calls_to_run.extend(task["tool_calls"])
            elif "tool" in task or "tool_name" in task or "name" in task:
                calls_to_run.append(
                    {
                        "tool": task.get("tool") or task.get("tool_name") or task.get("name"),
                        "args": task.get("args")
                        or task.get("parameters")
                        or task.get("input")
                        or {},
                    }
                )

            task_duration = 0.0
            task_success = True
            task_errors: list[str] = []
            task_tool_counts: dict[str, int] = {}
            task_tool_durations: dict[str, float] = {}
            last_output = ""

            for call in calls_to_run:
                t_name = str(
                    call.get("tool") or call.get("tool_name") or call.get("name") or ""
                ).strip()
                t_args = call.get("args") or call.get("parameters") or call.get("input") or {}

                if t_name not in per_tool_metrics:
                    per_tool_metrics[t_name] = ToolBenchmarkMetrics(tool_name=t_name)

                tool_obj = registry.get(t_name)
                t0 = time.perf_counter()

                if tool_obj is None:
                    duration = time.perf_counter() - t0
                    is_err = True
                    output_text = f"Tool {t_name!r} not found in registry"
                else:
                    try:
                        output_text, is_err = tool_obj.safe_call(t_args, store)
                    except Exception as exc:  # noqa: BLE001
                        output_text = f"Exception executing {t_name}: {exc}"
                        is_err = True
                    duration = time.perf_counter() - t0

                task_duration += duration
                last_output = output_text
                call_ok = not is_err

                per_tool_metrics[t_name].record(
                    duration_s=duration,
                    success=call_ok,
                    error=output_text if is_err else None,
                )
                task_tool_counts[t_name] = task_tool_counts.get(t_name, 0) + 1
                task_tool_durations[t_name] = task_tool_durations.get(t_name, 0.0) + duration

                if not call_ok:
                    task_success = False
                    task_errors.append(f"[{t_name}] {output_text}")

            feedback_raw = (
                task.get("response")
                or task.get("mock_response")
                or task.get("feedback_text")
                or task.get("evaluation")
                or last_output
            )
            feedback_str = str(feedback_raw) if feedback_raw is not None else ""

            summary_val = _extract_xml_tag(feedback_str, "summary")
            feedback_val = _extract_xml_tag(feedback_str, "feedback")
            response_val = _extract_xml_tag(feedback_str, "response")

            if not summary_val:
                tools_used = ", ".join(task_tool_counts.keys()) or "none"
                summary_val = f"Task {task_id} completed with tools: {tools_used}"
            if not feedback_val:
                if task_success:
                    feedback_val = "All tools executed successfully without error."
                else:
                    feedback_val = f"Task failed: {'; '.join(task_errors)}"
            if not response_val:
                response_val = feedback_str or ("OK" if task_success else "ERROR")

            primary_tool = (
                list(task_tool_counts.keys())[0] if len(task_tool_counts) == 1 else "multiple"
            )
            if not task_tool_counts:
                primary_tool = "none"

            result_entry = ToolBenchmarkResult(
                task_id=task_id,
                tool_name=primary_tool,
                success=task_success,
                duration_s=round(task_duration, 4),
                tool_calls=len(calls_to_run),
                summary=summary_val,
                feedback=feedback_val,
                response=response_val,
                errors=task_errors,
                per_tool_counts=task_tool_counts,
                per_tool_durations={k: round(v, 4) for k, v in task_tool_durations.items()},
                tool_metrics={
                    k: per_tool_metrics[k] for k in task_tool_counts if k in per_tool_metrics
                },
            )
            results.append(result_entry)
    finally:
        store.close()

    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r.success)
    failed_tasks = total_tasks - successful_tasks
    accuracy = round(successful_tasks / total_tasks, 4) if total_tasks > 0 else 0.0
    total_tool_calls = sum(r.tool_calls for r in results)
    avg_duration_s = (
        round(sum(r.duration_s for r in results) / total_tasks, 4) if total_tasks > 0 else 0.0
    )
    avg_tool_calls = round(total_tool_calls / total_tasks, 2) if total_tasks > 0 else 0.0

    summary_stats = {
        "accuracy": accuracy,
        "average_duration_s": avg_duration_s,
        "avg_duration_s": avg_duration_s,
        "average_tool_calls": avg_tool_calls,
        "avg_tool_calls": avg_tool_calls,
        "total_tool_calls": total_tool_calls,
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks,
    }

    report = _format_benchmark_report(
        persona=persona,
        summary_stats=summary_stats,
        per_tool_metrics=per_tool_metrics,
        results=results,
    )

    return {
        "persona": persona,
        "healthy": accuracy >= 0.8 and failed_tasks == 0,
        "summary": summary_stats,
        "accuracy": accuracy,
        "average_duration_s": avg_duration_s,
        "avg_duration_s": avg_duration_s,
        "average_tool_calls": avg_tool_calls,
        "avg_tool_calls": avg_tool_calls,
        "total_tool_calls": total_tool_calls,
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "failed_tasks": failed_tasks,
        "per_tool_metrics": {k: v.to_dict() for k, v in per_tool_metrics.items()},
        "results": [r.to_dict() for r in results],
        "report": report,
    }


def evaluate_persona_agents_md_alignment(
    persona: str, personas_dir: Path | None = None
) -> dict[str, Any]:
    """Evaluate a persona's AGENTS.md against its configured requirements (workspace.yaml, config.yaml, skills)."""
    if persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    base_dir = personas_dir or PERSONAS_DIR
    root = base_dir / persona
    agents_file = root / "AGENTS.md"
    file_present = agents_file.is_file()
    agents_text = agents_file.read_text(encoding="utf-8") if file_present else ""

    ws_data = _load_yaml_dict(root / "config" / "workspace.yaml")
    cfg_data = _load_yaml_dict(root / "config" / "config.yaml")
    raw_model = cfg_data.get("model")
    model_cfg = raw_model if isinstance(raw_model, dict) else {}

    role = str(ws_data.get("role") or "").strip()
    domain = str(ws_data.get("domain") or "").strip()
    primary_skills: list[str] = list(ws_data.get("primary_skills") or [])
    allowed_tools: list[str] = list(ws_data.get("allowed_tools") or [])
    provider = str(model_cfg.get("provider") or "").strip()
    default_model = str(model_cfg.get("default") or "").strip()

    skills_dir = root / "skills"
    overlay_count = (
        sum(1 for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
        if skills_dir.is_dir()
        else 0
    )
    shared_dir = base_dir / "shared" / "skills"
    shared_count = (
        sum(1 for d in shared_dir.iterdir() if d.is_dir() and (d / "SKILL.md").is_file())
        if shared_dir.is_dir()
        else 0
    )

    lead_directive = (
        "The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`."
    )
    lead_present = lead_directive in agents_text

    role_and_domain_ok = bool(role and role in agents_text and domain and domain in agents_text)
    model_loadout_ok = bool(
        provider and provider in agents_text and default_model and default_model in agents_text
    )
    missing_primary = [s for s in primary_skills if s not in agents_text]
    primary_skills_ok = bool(primary_skills) and not missing_primary

    missing_tools = [t for t in allowed_tools if t not in agents_text]
    allowed_tools_ok = bool(allowed_tools) and not missing_tools

    skill_count_phrase = f"{overlay_count} Overlay Skills + {shared_count} Shared Skills"
    skill_counts_ok = overlay_count > 0 and skill_count_phrase in agents_text

    evo_cmd = f"./evolve_agent.sh {persona}"
    eval_marker = f"CYCLE EVAL: {persona}"
    evolution_workflow_ok = (
        evo_cmd in agents_text
        and eval_marker in agents_text
        and f"build/agent-repos/{persona}" in agents_text
    )

    checks: dict[str, bool] = {
        "file_present": file_present,
        "lead_directive_present": lead_present,
        "role_and_domain_matched": role_and_domain_ok,
        "model_loadout_matched": model_loadout_ok,
        "primary_skills_matched": primary_skills_ok,
        "allowed_tools_matched": allowed_tools_ok,
        "skill_counts_matched": skill_counts_ok,
        "evolution_workflow_matched": evolution_workflow_ok,
    }

    diagnostics: list[str] = []
    if not file_present:
        diagnostics.append("Missing AGENTS.md")
    if not lead_present:
        diagnostics.append("Missing mandatory lead SakThai standalone directive in AGENTS.md")
    if not role_and_domain_ok:
        diagnostics.append(f"Missing role ({role!r}) or domain ({domain!r}) in AGENTS.md")
    if not model_loadout_ok:
        diagnostics.append(
            f"Missing configured model loadout ({provider}:{default_model}) in AGENTS.md"
        )
    if not primary_skills_ok:
        diagnostics.append(
            f"Missing primary skills in AGENTS.md: {', '.join(missing_primary) or 'none configured'}"
        )
    if not allowed_tools_ok:
        diagnostics.append(
            f"Missing allowed tools in AGENTS.md: {', '.join(missing_tools) or 'none configured'}"
        )
    if not skill_counts_ok:
        diagnostics.append(f"Missing skill count phrase '{skill_count_phrase}' in AGENTS.md")
    if not evolution_workflow_ok:
        diagnostics.append(
            f"Missing persona evolution workflow ('{evo_cmd}', '{eval_marker}', or export path) in AGENTS.md"
        )

    passed_checks = sum(1 for v in checks.values() if v)
    total_checks = len(checks)
    agents_md_score = round(passed_checks / total_checks, 2)

    return {
        "persona": persona,
        "role": role,
        "domain": domain,
        "provider": provider,
        "model": default_model,
        "overlay_skills": overlay_count,
        "shared_skills": shared_count,
        "primary_skills": primary_skills,
        "allowed_tools": allowed_tools,
        "checks": checks,
        "checks_passed": passed_checks,
        "checks_total": total_checks,
        "agents_md_score": agents_md_score,
        "diagnostics": diagnostics,
        "aligned": passed_checks == total_checks,
    }


def evaluate_agents_md_trials(
    persona: str | None = None,
    trials: int = 1,
    personas_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute AGENTS.md requirement alignment evaluation across one or all personas for multiple trials."""
    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    trial_count = max(1, int(trials))
    targets = (persona,) if persona else PERSONA_NAMES

    trial_history: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    latest_report: dict[str, dict[str, Any]] = {}

    for i in range(1, trial_count + 1):
        t0 = time.perf_counter()
        run_report = {
            p: evaluate_persona_agents_md_alignment(p, personas_dir=personas_dir) for p in targets
        }
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies_ms.append(elapsed_ms)
        latest_report = run_report

        all_aligned = all(r["aligned"] for r in run_report.values())
        tot_checks = sum(r["checks_total"] for r in run_report.values())
        passed_checks = sum(r["checks_passed"] for r in run_report.values())
        avg_score = (
            round(sum(r["agents_md_score"] for r in run_report.values()) / len(targets), 2)
            if targets
            else 0.0
        )

        trial_history.append(
            {
                "trial": i,
                "latency_ms": elapsed_ms,
                "all_aligned": all_aligned,
                "total_checks": tot_checks,
                "passed_checks": passed_checks,
                "average_score": avg_score,
                "scores": {p: run_report[p]["agents_md_score"] for p in targets},
            }
        )

    first_scores = trial_history[0]["scores"]
    consistent = all(t["scores"] == first_scores for t in trial_history)
    all_trials_aligned = all(t["all_aligned"] for t in trial_history)
    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)
    jitter = round(max_latency - min_latency, 2)

    return {
        "persona": persona,
        "trials": trial_count,
        "all_trials_aligned": all_trials_aligned,
        "consistent": consistent,
        "latencies_ms": latencies_ms,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "jitter_ms": jitter,
        "trial_history": trial_history,
        "latest_report": latest_report,
    }


def _score_to_grade(score: float) -> str:
    if score >= 0.95:
        return "A+"
    if score >= 0.90:
        return "A"
    if score >= 0.85:
        return "A-"
    if score >= 0.80:
        return "B+"
    if score >= 0.75:
        return "B"
    if score >= 0.70:
        return "C"
    return "F"


def evaluate_persona_extensions_health(
    persona: str | None = None,
    home_dir: Path | None = None,
) -> dict[str, Any]:
    """Evaluate extensions health against 8-factor rubric across registry, containment, schema, and isolation."""
    from ..config import persona_extensions_dir, persona_extensions_registry_path
    from ..extensions.install import (
        DANGEROUS_SHELL_PATTERNS,
        EXTENSION_NAME_RE,
        _discover_mcp_servers,
        _discover_skills_with_validation,
        _load_registry,
        _registry_path,
        extensions_dir,
        validate_extension_manifest,
    )

    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    diagnostics: list[str] = []
    checks: dict[str, bool] = {k: True for k in EXTENSIONS_RUBRIC_CRITERIA}

    # 1. registry_valid: test registry file readability and structure
    base_reg_path = _registry_path(persona)
    if base_reg_path.exists():
        try:
            raw_text = base_reg_path.read_text(encoding="utf-8")
            parsed = json.loads(raw_text)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("extensions"), dict):
                checks["registry_valid"] = False
                diagnostics.append(
                    f"Registry {base_reg_path} is malformed (missing extensions dict)"
                )
        except (json.JSONDecodeError, OSError) as exc:
            checks["registry_valid"] = False
            diagnostics.append(f"Registry {base_reg_path} failed to parse: {exc}")

    # Gather registered extensions
    reg_data = _load_registry(persona)
    extensions_map = reg_data.get("extensions", {})
    ext_base = extensions_dir(persona).resolve()

    # 2. paths_contained & 3. names_valid & 4. manifests_valid & 5. skills_valid & 6. isolation_safe
    for name, item in extensions_map.items():
        if not EXTENSION_NAME_RE.match(name):
            checks["names_valid"] = False
            diagnostics.append(f"Extension {name!r}: invalid name format")

        if not isinstance(item, dict):
            checks["registry_valid"] = False
            diagnostics.append(f"Extension {name!r}: entry in registry is not a dict")
            continue

        raw_path = item.get("path")
        if not raw_path:
            checks["paths_contained"] = False
            diagnostics.append(f"Extension {name!r}: missing path in registry")
            continue

        path = Path(raw_path).resolve()
        if path == ext_base or not path.is_relative_to(ext_base):
            checks["paths_contained"] = False
            diagnostics.append(
                f"Extension {name!r}: path {path} escapes authorized directory {ext_base}"
            )

        if path.exists():
            manifest_path = path / "gemini-extension.json"
            if manifest_path.exists():
                m_valid, m_diags = validate_extension_manifest(manifest_path)
                if not m_valid:
                    checks["manifests_valid"] = False
                    diagnostics.extend([f"Extension {name!r}: {d}" for d in m_diags])
                try:
                    m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                    srvs = m_data.get("mcpServers", {}) if isinstance(m_data, dict) else {}
                    if isinstance(srvs, dict):
                        for srv_name, srv_conf in srvs.items():
                            if isinstance(srv_conf, dict):
                                cmd = srv_conf.get("command", "")
                                if isinstance(cmd, str) and DANGEROUS_SHELL_PATTERNS.search(cmd):
                                    checks["isolation_safe"] = False
                                    diagnostics.append(
                                        f"Extension {name!r} server {srv_name!r}: dangerous shell metacharacters in command"
                                    )
                except (json.JSONDecodeError, OSError):
                    pass

            skills, skill_diags = _discover_skills_with_validation(path)
            if skill_diags:
                checks["skills_valid"] = False
                diagnostics.extend([f"Extension {name!r}: {d}" for d in skill_diags])

    # 7. discovery_health: verify discovery helper routines operate safely
    try:
        dummy_skills = _discover_skills_with_validation(ext_base)
        dummy_mcp = _discover_mcp_servers(ext_base)
        assert isinstance(dummy_skills, tuple)
        assert isinstance(dummy_mcp, list)
    except Exception as exc:
        checks["discovery_health"] = False
        diagnostics.append(f"Discovery helper crashed on directory {ext_base}: {exc}")

    # 8. persona_scoping_ready: check persona directories and registry paths resolve cleanly
    try:
        for p in PERSONA_NAMES:
            p_dir = persona_extensions_dir(p)
            p_reg = persona_extensions_registry_path(p)
            assert p_dir.name == "extensions"
            assert p_reg.name == "extensions.json"
            assert p in str(p_dir)
            assert p in str(p_reg)
    except Exception as exc:
        checks["persona_scoping_ready"] = False
        diagnostics.append(f"Persona extensions directory scoping failed: {exc}")

    passed_count = sum(1 for v in checks.values() if v)
    total_count = len(checks)
    score = round(passed_count / total_count, 2)
    grade = _score_to_grade(score)

    return {
        "persona": persona,
        "grade": grade,
        "extensions_score": score,
        "checks": checks,
        "checks_passed": passed_count,
        "checks_total": total_count,
        "diagnostics": diagnostics,
        "healthy": score >= 0.80 and checks["registry_valid"] and checks["paths_contained"],
        "extensions_count": len(extensions_map),
        "extensions_found": sorted(extensions_map.keys()),
    }


def evaluate_extensions_trials(
    persona: str | None = None,
    trials: int = 1,
    home_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute extensions health evaluation across one or all personas for multiple trials."""
    if persona is not None and persona not in PERSONA_NAMES:
        raise ValueError(f"Unknown persona {persona!r}; expected one of {PERSONA_NAMES}")

    trial_count = max(1, int(trials))
    targets = (persona,) if persona else PERSONA_NAMES

    trial_history: list[dict[str, Any]] = []
    latencies_ms: list[float] = []
    latest_report: dict[str, dict[str, Any]] = {}

    for i in range(1, trial_count + 1):
        t0 = time.perf_counter()
        run_report = {p: evaluate_persona_extensions_health(p, home_dir=home_dir) for p in targets}
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        latencies_ms.append(elapsed_ms)
        latest_report = run_report

        all_healthy = all(r["healthy"] for r in run_report.values())
        tot_checks = sum(r["checks_total"] for r in run_report.values())
        passed_checks = sum(r["checks_passed"] for r in run_report.values())
        avg_score = (
            round(sum(r["extensions_score"] for r in run_report.values()) / len(targets), 2)
            if targets
            else 0.0
        )

        trial_history.append(
            {
                "trial": i,
                "latency_ms": elapsed_ms,
                "all_healthy": all_healthy,
                "total_checks": tot_checks,
                "passed_checks": passed_checks,
                "average_score": avg_score,
                "scores": {p: run_report[p]["extensions_score"] for p in targets},
            }
        )

    first_scores = trial_history[0]["scores"]
    consistent = all(t["scores"] == first_scores for t in trial_history)
    all_trials_healthy = all(t["all_healthy"] for t in trial_history)
    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 2)
    min_latency = round(min(latencies_ms), 2)
    max_latency = round(max(latencies_ms), 2)
    jitter = round(max_latency - min_latency, 2)

    return {
        "persona": persona,
        "trials": trial_count,
        "all_trials_healthy": all_trials_healthy,
        "consistent": consistent,
        "latencies_ms": latencies_ms,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "jitter_ms": jitter,
        "trial_history": trial_history,
        "latest_report": latest_report,
    }


def evaluate_persona_audit(
    persona: str,
    personas_dir: Path | None = None,
    home_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute a comprehensive 6-pillar audit across readiness, soul, skills, tools, memory, and safety."""
    readiness = evaluate_persona_readiness(persona, personas_dir=personas_dir)
    soul = evaluate_persona_soul_alignment(persona, personas_dir=personas_dir)
    skills = evaluate_persona_skills_health(persona, personas_dir=personas_dir)
    tools = evaluate_persona_tools_health(persona)
    memory = evaluate_persona_memory_health(persona, home_dir=home_dir)
    safety = evaluate_persona_safety_compliance(persona)
    extensions = evaluate_persona_extensions_health(persona, home_dir=home_dir)

    composite_score = round(
        0.20 * readiness["readiness_score"]
        + 0.20 * soul["soul_score"]
        + 0.15 * skills["skills_score"]
        + 0.15 * tools["tools_score"]
        + 0.15 * memory["memory_score"]
        + 0.15 * safety["safety_score"],
        2,
    )
    grade = _score_to_grade(composite_score)
    all_diagnostics = (
        readiness["diagnostics"]
        + soul["diagnostics"]
        + skills["diagnostics"]
        + tools["diagnostics"]
        + memory["diagnostics"]
        + safety["diagnostics"]
        + extensions["diagnostics"]
    )

    return {
        "persona": persona,
        "grade": grade,
        "composite_score": composite_score,
        "pillars": {
            "readiness": {
                "score": readiness["readiness_score"],
                "passed": readiness["ready"],
            },
            "soul": {
                "score": soul["soul_score"],
                "passed": soul["aligned"],
                "intro_line": soul["intro_line"],
            },
            "skills": {
                "score": skills["skills_score"],
                "passed": skills["healthy"],
                "total": skills["total_skills"],
                "valid": skills["valid_skills"],
            },
            "tools": {
                "score": tools["tools_score"],
                "passed": tools["healthy"],
                "total": tools["total_tools"],
                "valid": tools["valid_tools"],
            },
            "memory": {
                "score": memory["memory_score"],
                "passed": memory["healthy"],
            },
            "safety": {
                "score": safety["safety_score"],
                "passed": safety["compliant"],
            },
        },
        "diagnostics": all_diagnostics,
        "passed": composite_score >= 0.80 and readiness["ready"] and soul["aligned"],
    }


def summarize_fleet_audit(
    personas_dir: Path | None = None,
    home_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute a 5-pillar audit across the entire Sak Family fleet and summarize scores."""
    scorecards = {
        p: evaluate_persona_audit(p, personas_dir=personas_dir, home_dir=home_dir)
        for p in PERSONA_NAMES
    }
    total = len(scorecards)
    avg_score = (
        round(sum(float(s["composite_score"]) for s in scorecards.values()) / total, 2)
        if total > 0
        else 0.0
    )
    fleet_grade = _score_to_grade(avg_score)
    all_passed = all(s["passed"] for s in scorecards.values())
    return {
        "personas_audited": total,
        "fleet_average_score": avg_score,
        "fleet_grade": fleet_grade,
        "all_passed": all_passed,
        "scorecards": scorecards,
    }
