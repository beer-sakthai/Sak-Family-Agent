"""Payload builders for the read-only web API.

Pure functions: no HTTP, no globals, every input injectable. ``web/server.py``
is the thin dispatcher on top; keeping the construction here is what makes it
testable without a socket, the same split ``mcp/server.py:handle_request`` uses.

Every builder returns a shape declared in :mod:`sakthai.web.contracts`, which is
the single definition the TypeScript dashboard's types are generated from.

**Nothing here re-parses a file the package already knows how to read.**
Metrics wrap :func:`~sakthai.agent.eval.summarize_evals`, memory goes through
:class:`~sakthai.memory.merged.FamilyMemoryView` and ``MemoryStore``'s own
aggregate queries, sessions reuse the session-log schema and
:func:`~sakthai.memory.session_search.search_sessions`'s notion of searchable
text. A second parser is a second thing to keep in sync.

**Sharded runtime state.** In production each persona runs with
``SAKTHAI_HOME=$HOME/.sakthai/$AGENT`` (see ``infra/vm-agents/``), so its
``eval.jsonl``, ``sessions/`` and ``audit.log`` live under its own subdirectory
rather than the unscoped root. Every reader here walks the unscoped root *and*
each persona subdirectory, and treats a record's location as attribution when
the record itself carries none.
"""

from __future__ import annotations

import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..agent.eval import read_records, summarize_evals
from ..config import (
    PERSONA_NAMES,
    memory_db_path,
    persona_memory_db_path,
    persona_model_defaults,
    sakthai_home,
)
from ..config import workflow_runs_dir as config_workflow_runs_dir
from ..memory.merged import FamilyMemoryView
from ..memory.store import MemoryStore
from .contracts import (
    UNATTRIBUTED,
    ApiEnvelope,
    AuditEvent,
    AuditPayload,
    DataSource,
    FactRecord,
    GrowthSeries,
    MemoryPayload,
    MetricsPayload,
    ModelUsage,
    ObservationRecord,
    PersonasPayload,
    PersonaSummary,
    SessionDetail,
    SessionMessage,
    SessionsPayload,
    SessionSummary,
    TokenStats,
    ToolCallRecord,
    TrendPoint,
    WorkflowRunDetail,
    WorkflowRunSummary,
    WorkflowsPayload,
    WorkflowStepResult,
)

#: How many eval records any one aggregate considers. The log is append-only and
#: unbounded; a dashboard does not need its whole history.
EVAL_WINDOW = 2000

#: Ceiling on session files parsed per request. Session logs are read newest
#: first (the filename's epoch prefix sorts correctly), so this bounds the work
#: without hiding recent activity.
MAX_SESSION_SCAN = 500

#: Ceiling on audit-log lines read per request.
MAX_AUDIT_LINES = 2000

#: Rows fed to MemoryStore's aggregate queries, matching dashboard/data.py.
MEMORY_ROW_LIMIT = 1000

_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


# -- envelope -------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def envelope(data: Any, source: DataSource = "local") -> ApiEnvelope[Any]:
    """Wrap a payload so the client always knows where the data came from."""
    return {"ok": True, "source": source, "generated_at": _now_iso(), "data": data}


# -- shared path resolution ----------------------------------------------


def display_name(persona: str) -> str:
    """``"sakthai"`` -> ``"SakThai"``. Holds for all six names in PERSONA_NAMES."""
    return "Sak" + persona[3:].capitalize()


def runtime_roots(home: Path | None = None) -> list[tuple[str | None, Path]]:
    """The unscoped root plus each persona's own root, as ``(persona, path)``.

    ``persona`` is None for the unscoped root: state there was written by a
    process that was not persona-scoped, so its location attributes nothing.
    """
    base = home if home is not None else sakthai_home()
    roots: list[tuple[str | None, Path]] = [(None, base)]
    roots.extend((persona, base / persona) for persona in PERSONA_NAMES)
    return roots


def _shard_paths(home: Path | None = None) -> dict[str, Path]:
    """Where each memory shard lives, mirroring FamilyMemoryView's convention."""
    if home is None:
        paths = {p: persona_memory_db_path(p) for p in PERSONA_NAMES}
        paths["shared"] = memory_db_path()
        return paths
    paths = {p: home / p / "memory.db" for p in PERSONA_NAMES}
    paths["shared"] = home / "memory.db"
    return paths


def _as_dict(value: Any) -> dict[str, Any]:
    """Narrow a value read out of JSON to a dict, or an empty one.

    Session logs are written best-effort by a live agent, so a missing or
    wrong-typed sub-object is a shape to tolerate, not an error to raise.
    """
    return value if isinstance(value, dict) else {}


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    """Parse the last ``limit`` well-formed JSON objects from a JSONL file.

    Unparseable lines are skipped rather than failing the request — these logs
    are appended best-effort from a live agent and a torn final line is normal.
    """
    if not path.is_file():
        return []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in raw.splitlines()[-limit:]:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
    return records


# -- personas -------------------------------------------------------------


def _eval_records_with_attribution(
    home: Path | None = None,
) -> list[tuple[dict[str, Any], str | None]]:
    """Every eval record across all roots, paired with its attributed persona.

    A record's own ``persona`` field wins; failing that, an eval log found under
    a persona's own root attributes to that persona, because only that persona's
    process writes there. Records with neither stay None — the honest answer.
    """
    out: list[tuple[dict[str, Any], str | None]] = []
    for persona, root in runtime_roots(home):
        for record in read_records(root / "eval.jsonl", limit=EVAL_WINDOW):
            attributed = record.get("persona") or persona
            out.append((record, attributed if isinstance(attributed, str) else None))
    return out


def _blank_persona(persona: str) -> PersonaSummary:
    provider, model = persona_model_defaults(persona)
    return {
        "name": persona,
        "display_name": display_name(persona),
        "provider": provider or "",
        "model": model or "",
        "has_shard": False,
        "fact_count": 0,
        "observation_count": 0,
        "runs": 0,
        "errors": 0,
        "avg_latency_ms": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "last_run_at": None,
    }


def personas_payload(home: Path | None = None) -> PersonasPayload:
    """Every persona in ``config.PERSONA_NAMES`` — all six, present or not.

    A persona whose memory shard does not exist yet is reported with
    ``has_shard: False`` and zeroed counts rather than omitted: the shard file
    is only created on first write, so absence is a normal state.
    """
    summaries = {persona: _blank_persona(persona) for persona in PERSONA_NAMES}
    shard_paths = _shard_paths(home)

    for persona in PERSONA_NAMES:
        path = shard_paths[persona]
        if not path.exists():
            continue
        summaries[persona]["has_shard"] = True
        store = MemoryStore(path)
        try:
            stats = store.stats()
            summaries[persona]["fact_count"] = int(stats["facts"]["total"])
            summaries[persona]["observation_count"] = int(stats["observations"]["total"])
        finally:
            store.close()

    latency_totals: dict[str, float] = dict.fromkeys(PERSONA_NAMES, 0.0)
    unattributed = 0
    for record, attributed in _eval_records_with_attribution(home):
        if attributed is None or attributed not in summaries:
            unattributed += 1
            continue
        entry = summaries[attributed]
        entry["runs"] += 1
        entry["errors"] += 1 if record.get("had_error") else 0
        entry["input_tokens"] += int(record.get("input_tokens", 0) or 0)
        entry["output_tokens"] += int(record.get("output_tokens", 0) or 0)
        latency_totals[attributed] += float(record.get("latency_s", 0.0) or 0.0)
        timestamp = record.get("timestamp")
        if isinstance(timestamp, (int, float)):
            previous = entry["last_run_at"]
            entry["last_run_at"] = (
                int(timestamp) if previous is None else max(previous, int(timestamp))
            )

    for persona, entry in summaries.items():
        if entry["runs"]:
            entry["avg_latency_ms"] = round(latency_totals[persona] / entry["runs"] * 1000, 2)

    return {
        "personas": [summaries[persona] for persona in PERSONA_NAMES],
        "unattributed_runs": unattributed,
    }


# -- metrics --------------------------------------------------------------


def _empty_metrics() -> MetricsPayload:
    return {
        "total_runs": 0,
        "error_rate": 0.0,
        "avg_latency_ms": 0.0,
        "tokens": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "stop_reasons": {},
        "per_model": {},
        "trends": [],
    }


def _trends(records: list[dict[str, Any]]) -> list[TrendPoint]:
    """One point per UTC day present in the records, oldest first."""
    days: dict[str, TrendPoint] = {}
    latency: dict[str, float] = {}
    for record in records:
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            continue
        date = datetime.fromtimestamp(float(timestamp), tz=UTC).strftime("%Y-%m-%d")
        point = days.setdefault(
            date,
            {
                "date": date,
                "runs": 0,
                "errors": 0,
                "avg_latency_ms": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
            },
        )
        point["runs"] += 1
        point["errors"] += 1 if record.get("had_error") else 0
        point["input_tokens"] += int(record.get("input_tokens", 0) or 0)
        point["output_tokens"] += int(record.get("output_tokens", 0) or 0)
        latency[date] = latency.get(date, 0.0) + float(record.get("latency_s", 0.0) or 0.0)

    for date, point in days.items():
        point["avg_latency_ms"] = round(latency[date] / point["runs"] * 1000, 2)
    return [days[date] for date in sorted(days)]


def metrics_payload(
    limit: int = EVAL_WINDOW,
    personas: list[str] | None = None,
    home: Path | None = None,
) -> MetricsPayload:
    """Run/latency/token aggregates over the eval log across every root.

    Wraps :func:`summarize_evals` for the headline numbers rather than
    recomputing them, and adds the daily series and stop-reason histogram the
    dashboard charts need.

    ``personas`` narrows to those personas' runs, using the same attribution as
    :func:`personas_payload` — the record's own ``persona`` field, else the root
    its log was found under. A run attributed to nobody is *excluded* from a
    filtered view: it belongs to no persona, so it belongs to no persona's
    figures either.

    The filter is applied before ``limit``, so the window is the last N of that
    persona's runs rather than whichever of them fall inside the family's last
    N — otherwise a quiet persona would report nothing while a busy one filled
    the window.
    """
    attributed = _eval_records_with_attribution(home)
    if personas is not None:
        wanted = set(personas)
        attributed = [pair for pair in attributed if pair[1] in wanted]
    records = [record for record, _ in attributed][-limit:]
    if not records:
        return _empty_metrics()

    # summarize_evals owns the headline aggregation; feed it the same records by
    # pointing it at each root's log and merging, rather than re-deriving here.
    per_model: dict[str, ModelUsage] = {}
    model_latency: dict[str, float] = {}
    stop_reasons: dict[str, int] = {}
    errors = 0
    total_latency = 0.0
    tokens: TokenStats = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    for record in records:
        model = str(record.get("model", "") or "unknown")
        usage = per_model.setdefault(
            model, {"count": 0, "input_tokens": 0, "output_tokens": 0, "avg_latency_s": 0.0}
        )
        usage["count"] += 1
        usage["input_tokens"] += int(record.get("input_tokens", 0) or 0)
        usage["output_tokens"] += int(record.get("output_tokens", 0) or 0)
        model_latency[model] = model_latency.get(model, 0.0) + float(
            record.get("latency_s", 0.0) or 0.0
        )

        reason = str(record.get("stop_reason", "") or "unknown")
        stop_reasons[reason] = stop_reasons.get(reason, 0) + 1

        errors += 1 if record.get("had_error") else 0
        total_latency += float(record.get("latency_s", 0.0) or 0.0)
        tokens["input_tokens"] += int(record.get("input_tokens", 0) or 0)
        tokens["output_tokens"] += int(record.get("output_tokens", 0) or 0)

    tokens["total_tokens"] = tokens["input_tokens"] + tokens["output_tokens"]
    for model, usage in per_model.items():
        usage["avg_latency_s"] = round(model_latency[model] / usage["count"], 3)

    total = len(records)
    return {
        "total_runs": total,
        "error_rate": round(errors / total, 4),
        "avg_latency_ms": round(total_latency / total * 1000, 2),
        "tokens": tokens,
        "stop_reasons": stop_reasons,
        "per_model": per_model,
        "trends": _trends(records),
    }


def eval_summary(path: Path | None = None, limit: int = 50) -> dict[str, Any]:
    """Thin passthrough to :func:`summarize_evals` for the single-log view."""
    return summarize_evals(path=path, limit=limit)


# -- sessions -------------------------------------------------------------


def _session_summary(
    session_id: str, data: dict[str, Any], fallback_persona: str | None
) -> SessionSummary:
    result = _as_dict(data.get("result"))
    usage = _as_dict(data.get("usage"))
    tool_calls = result.get("tool_calls") or []
    messages = data.get("messages") or []
    persona = data.get("persona") or fallback_persona

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    return {
        "id": session_id,
        "timestamp": int(data.get("timestamp", 0) or 0),
        "persona": persona if isinstance(persona, str) else None,
        "task": str(data.get("task", "")),
        "model": str(data.get("model", "")),
        "iterations": int(result.get("iterations", 0) or 0),
        "stop_reason": str(result.get("stop_reason", "")),
        "tokens": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": int(usage.get("total_tokens", 0) or 0)
            or (input_tokens + output_tokens),
        },
        "message_count": len(messages) if isinstance(messages, list) else 0,
        "tool_call_count": len(tool_calls) if isinstance(tool_calls, list) else 0,
        "had_error": any(
            isinstance(call, dict) and call.get("is_error") for call in tool_calls or []
        ),
    }


def _flatten_content(content: Any) -> str:
    """Session messages hold either a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(str(block.get("text") or block.get("name") or block.get("type", "")))
            else:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    return str(content) if content is not None else ""


def _session_detail(summary: SessionSummary, data: dict[str, Any]) -> SessionDetail:
    result = _as_dict(data.get("result"))
    raw_messages = data.get("messages") or []
    messages: list[SessionMessage] = [
        {"role": str(m.get("role", "")), "content": _flatten_content(m.get("content"))}
        for m in raw_messages
        if isinstance(m, dict)
    ]
    tool_calls: list[ToolCallRecord] = [
        {"name": str(c.get("name", "")), "is_error": bool(c.get("is_error"))}
        for c in (result.get("tool_calls") or [])
        if isinstance(c, dict)
    ]
    return {
        "summary": summary,
        "messages": messages,
        "result_text": str(result.get("text", "")),
        "tool_calls": tool_calls,
    }


def _session_files(home: Path | None = None) -> list[tuple[Path, str | None]]:
    """Every session file across all roots, newest first.

    Filenames are ``<unix_seconds>_<uuid hex>.json``, so a reverse lexical sort
    on the stem is a reverse chronological sort — no stat call needed.
    """
    found: list[tuple[Path, str | None]] = []
    for persona, root in runtime_roots(home):
        directory = root / "sessions"
        if not directory.is_dir():
            continue
        found.extend((path, persona) for path in directory.glob("*.json"))
    found.sort(key=lambda pair: pair[0].stem, reverse=True)
    return found


def _load_session(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def parse_personas(raw: str | None) -> list[str] | None:
    """Narrow a ``persona=`` query value to known persona names.

    Accepts one name or a comma-separated list. Returns None for anything that
    names no persona we know — an absent filter, blank text, or a typo — so the
    caller falls back to the whole family rather than to an empty result that
    would read as "this persona has no data".
    """
    if not raw or not raw.strip():
        return None
    wanted = [part.strip().lower() for part in raw.split(",")]
    known = [name for name in PERSONA_NAMES if name in wanted]
    return known or None


def _matches(summary: SessionSummary, terms: list[str]) -> bool:
    haystack = f"{summary['id']} {summary['task']} {summary['model']} {summary['persona']}".lower()
    return all(term in haystack for term in terms)


def sessions_payload(
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
    session_id: str | None = None,
    personas: list[str] | None = None,
    home: Path | None = None,
) -> SessionsPayload:
    """A page of session summaries, plus one full transcript when asked for.

    ``limit``/``offset`` are clamped rather than trusted: a non-numeric limit
    reaching ``slice`` as NaN is exactly the bug this replaces on the TS side.

    ``personas`` narrows to those personas' runs. It is applied before both the
    search and the offset, so ``total`` counts the filtered set and paging
    through a filtered view lands on the right rows — filtering a page after
    slicing it would give a page-scoped answer wearing a global label.
    """
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    files = _session_files(home)
    summaries: list[SessionSummary] = []
    for path, persona in files[:MAX_SESSION_SCAN]:
        data = _load_session(path)
        if data is not None:
            summaries.append(_session_summary(path.stem, data, persona))

    if personas is not None:
        wanted = set(personas)
        summaries = [s for s in summaries if s["persona"] in wanted]

    if search and search.strip():
        terms = search.strip().lower().split()
        summaries = [s for s in summaries if _matches(s, terms)]

    detail: SessionDetail | None = None
    if session_id:
        detail = session_detail(session_id, home)
        # A filtered view must not open a transcript the filter excludes:
        # `?persona=sakthai&id=<a-saksee-session>` would otherwise render the
        # other persona's transcript in a drawer labelled as filtered.
        if (
            detail is not None
            and personas is not None
            and detail["summary"]["persona"] not in personas
        ):
            detail = None

    return {
        "sessions": summaries[offset : offset + limit],
        "total": len(summaries),
        "detail": detail,
    }


def session_detail(session_id: str, home: Path | None = None) -> SessionDetail | None:
    """One session's full transcript, or None if the id is unknown or unsafe.

    The id is pattern-checked before it ever reaches a path join — it arrives
    from a query string, and ``sessions/../../x`` must not resolve.

    Deliberately unscoped by persona: this is the raw lookup. Callers that hold
    a persona filter apply it themselves — see :func:`sessions_payload`.
    """
    if not _SESSION_ID_RE.match(session_id):
        return None
    for path, persona in _session_files(home):
        if path.stem != session_id:
            continue
        data = _load_session(path)
        if data is None:
            return None
        return _session_detail(_session_summary(session_id, data, persona), data)
    return None


# -- memory ---------------------------------------------------------------


def _fact_record(fact: Any, persona: str) -> FactRecord:
    return {
        "id": int(fact.id or 0),
        "persona": persona,
        "kind": fact.kind,
        "key": fact.key,
        "value": fact.value,
        "tags": list(fact.tags or []),
        "created_at": int(fact.created_at),
        "updated_at": int(fact.updated_at),
    }


def _observation_record(obs: Any, persona: str) -> ObservationRecord:
    return {
        "id": int(obs.id or 0),
        "persona": persona,
        "summary": obs.summary,
        "weight": float(obs.weight),
        "confidence": float(obs.confidence),
        "created_at": int(obs.created_at),
    }


def _growth(aggregate: dict[str, Any], start_ts: int) -> GrowthSeries:
    """Turn MemoryStore's 30 daily bins into a labelled cumulative series."""
    bins: list[int] = list(aggregate.get("bins") or [])
    running = int(aggregate.get("before_start", 0) or 0)
    labels: list[str] = []
    values: list[int] = []
    for index, count in enumerate(bins):
        running += int(count)
        day = datetime.fromtimestamp(start_ts + index * 86400, tz=UTC)
        labels.append(day.strftime("%Y-%m-%d"))
        values.append(running)
    return {"labels": labels, "values": values}


def memory_payload(
    query: str | None = None,
    personas: list[str] | None = None,
    limit: int = 100,
    home: Path | None = None,
) -> MemoryPayload:
    """Facts and observations merged across every persona shard.

    Uses ``get_dashboard_aggregates`` for the growth series that
    ``dashboard/data.py`` has always returned empty, summing across shards.

    ``personas`` narrows both the rows and the totals. It previously scoped only
    the rows — ``FamilyMemoryView`` took the filter but the aggregate loop did
    not — so a filtered request answered one persona's facts under the whole
    family's counts.
    """
    limit = max(1, min(500, limit))
    shard_paths = _shard_paths(home)
    # The aggregate loop below reads these paths directly, so it takes the
    # filtered map. `shard_paths` itself stays whole and is handed to
    # FamilyMemoryView untouched: dropping a key there would not exclude that
    # shard, it would send the view to the real ~/.sakthai instead.
    aggregate_paths = (
        {name: path for name, path in shard_paths.items() if name in set(personas)}
        if personas is not None
        else shard_paths
    )
    now = int(time.time())
    start_ts = now - 30 * 86400
    week_ago = now - 7 * 86400

    totals = {"facts": 0, "observations": 0}
    this_week = {"facts": 0, "observations": 0}
    growth_bins = {"facts": [0] * 30, "observations": [0] * 30}
    before_start = {"facts": 0, "observations": 0}
    kind_counts: dict[str, int] = {}

    for path in aggregate_paths.values():
        if not path.exists():
            continue
        store = MemoryStore(path)
        try:
            for table in ("facts", "observations"):
                aggregate = store.get_dashboard_aggregates(
                    table, MEMORY_ROW_LIMIT, start_ts, week_ago
                )
                totals[table] += int(aggregate.get("total", 0) or 0)
                this_week[table] += int(aggregate.get("this_week", 0) or 0)
                before_start[table] += int(aggregate.get("before_start", 0) or 0)
                for index, count in enumerate(aggregate.get("bins") or []):
                    if index < 30:
                        growth_bins[table][index] += int(count)
            for kind, count in store.get_fact_kind_counts(MEMORY_ROW_LIMIT).items():
                kind_counts[kind] = kind_counts.get(kind, 0) + count
        finally:
            store.close()

    # A persona-filtered view is that persona's own memory; the unscoped
    # legacy store is attributed to nobody, so it is excluded alongside the
    # other personas' shards.
    view = FamilyMemoryView(personas, shard_paths=shard_paths, include_unscoped=personas is None)
    try:
        if query and query.strip():
            sharded_facts, sharded_obs = view.search(query.strip(), limit=limit)
        else:
            sharded_facts = view.list_facts(limit=limit)
            sharded_obs = view.top_observations(limit=limit)
    finally:
        view.close()

    return {
        "facts": [_fact_record(sf.fact, sf.persona) for sf in sharded_facts],
        "observations": [_observation_record(so.observation, so.persona) for so in sharded_obs],
        "total_facts": totals["facts"],
        "total_observations": totals["observations"],
        "facts_this_week": this_week["facts"],
        "observations_this_week": this_week["observations"],
        "fact_growth": _growth(
            {"bins": growth_bins["facts"], "before_start": before_start["facts"]}, start_ts
        ),
        "observation_growth": _growth(
            {"bins": growth_bins["observations"], "before_start": before_start["observations"]},
            start_ts,
        ),
        "kind_counts": kind_counts,
    }


# -- audit ----------------------------------------------------------------


def _audit_event(raw: dict[str, Any]) -> AuditEvent:
    details = raw.get("details")
    return {
        "timestamp": float(raw.get("timestamp", 0.0) or 0.0),
        "type": str(raw.get("type", "")),
        "severity": str(raw.get("severity", "") or "low"),
        "message": str(raw.get("message", "")),
        "details": details if isinstance(details, dict) else {},
    }


def audit_payload(
    severity: str | None = None,
    limit: int = 200,
    personas: list[str] | None = None,
    home: Path | None = None,
) -> AuditPayload:
    """Security audit events from every root's ``audit.log``, newest first.

    An unrecognised ``severity`` filter matches nothing and says so through
    ``total: 0`` — it does not silently fall back to returning everything, which
    is how the TypeScript reader currently behaves.

    ``personas`` narrows to the logs under those personas' own roots. An
    ``AuditEvent`` carries no persona of its own, so the attribution is
    positional: only that persona's process writes to that root. The unscoped
    root is excluded under a filter, for the same reason it is in
    :func:`memory_payload` — it is attributed to nobody.
    """
    limit = max(1, min(1000, limit))
    wanted_personas = set(personas) if personas is not None else None
    events: list[AuditEvent] = []
    for persona, root in runtime_roots(home):
        if wanted_personas is not None and persona not in wanted_personas:
            continue
        events.extend(_audit_event(raw) for raw in _read_jsonl(root / "audit.log", MAX_AUDIT_LINES))

    severity_counts: dict[str, int] = {}
    for event in events:
        severity_counts[event["severity"]] = severity_counts.get(event["severity"], 0) + 1

    if severity:
        wanted = severity.strip().lower()
        events = [event for event in events if event["severity"].lower() == wanted]

    events.sort(key=lambda event: event["timestamp"], reverse=True)
    return {
        "events": events[:limit],
        "severity_counts": severity_counts,
        "total": len(events),
    }


# -- workflows ------------------------------------------------------------


def _duration_seconds(started: str | None, finished: str | None) -> float | None:
    """Elapsed seconds between two ISO-8601 stamps, or None if either is absent."""
    if not started or not finished:
        return None
    try:
        delta = datetime.fromisoformat(finished) - datetime.fromisoformat(started)
    except (TypeError, ValueError):
        return None
    return max(0.0, delta.total_seconds())


def _workflow_summary(run_id: str, data: dict[str, Any]) -> WorkflowRunSummary:
    steps = _as_dict(data.get("step_results"))
    started = data.get("start_time")
    finished = data.get("end_time")
    return {
        "run_id": run_id,
        "workflow_name": str(data.get("workflow_name", "")),
        # RunStatus/StepStatus serialise as UPPERCASE; lowercased here so the
        # client has one canonical form. Lossless — both are closed enums.
        "status": str(data.get("status", "")).lower(),
        "started_at": started if isinstance(started, str) else None,
        "finished_at": finished if isinstance(finished, str) else None,
        "duration_seconds": _duration_seconds(
            started if isinstance(started, str) else None,
            finished if isinstance(finished, str) else None,
        ),
        "step_count": len(steps),
        "failed_steps": sum(
            1
            for step in steps.values()
            if str(_as_dict(step).get("status", "")).lower() == "failed"
        ),
    }


def _workflow_step(data: dict[str, Any]) -> WorkflowStepResult:
    started = data.get("start_time")
    finished = data.get("end_time")
    error = data.get("error")
    return {
        "step_id": str(data.get("step_id", "")),
        "status": str(data.get("status", "")).lower(),
        "attempts": int(data.get("attempts", 0) or 0),
        "error": error if isinstance(error, str) else None,
        "started_at": started if isinstance(started, str) else None,
        "finished_at": finished if isinstance(finished, str) else None,
        "duration_seconds": _duration_seconds(
            started if isinstance(started, str) else None,
            finished if isinstance(finished, str) else None,
        ),
    }


def workflow_runs_dir(home: Path | None = None) -> Path:
    """Where ``agent_workflow`` writes its run histories."""
    return (home / "workflow_runs") if home is not None else config_workflow_runs_dir()


def workflows_payload(limit: int = 100, home: Path | None = None) -> WorkflowsPayload:
    """Workflow run summaries, newest first.

    Reads the JSON files ``agent_workflow.persistence.RunHistoryStore`` writes.
    The framework is not imported: it is a separate package outside
    this one's dependency graph, and its on-disk format is the contract.
    """
    limit = max(1, min(500, limit))
    directory = workflow_runs_dir(home)
    if not directory.is_dir():
        return {"runs": []}

    runs: list[WorkflowRunSummary] = []
    for path in directory.glob("*.json"):
        data = _load_session(path)
        if data is not None:
            runs.append(_workflow_summary(path.stem, data))
    runs.sort(key=lambda run: run["started_at"] or "", reverse=True)
    return {"runs": runs[:limit]}


def workflow_detail(run_id: str, home: Path | None = None) -> WorkflowRunDetail | None:
    """One run's full step history, or None if unknown.

    The id is pattern-checked before it reaches a path join — it arrives from a
    query string, mirroring ``RunHistoryStore._sanitize_run_id``'s own guard.
    """
    if not _SESSION_ID_RE.match(run_id):
        return None
    path = workflow_runs_dir(home) / f"{run_id}.json"
    if not path.is_file():
        return None
    data = _load_session(path)
    if data is None:
        return None
    steps = _as_dict(data.get("step_results"))
    return {
        "summary": _workflow_summary(run_id, data),
        "steps": [_workflow_step(_as_dict(step)) for step in steps.values()],
    }


__all__ = [
    "EVAL_WINDOW",
    "MAX_AUDIT_LINES",
    "MAX_SESSION_SCAN",
    "MEMORY_ROW_LIMIT",
    "UNATTRIBUTED",
    "audit_payload",
    "display_name",
    "envelope",
    "eval_summary",
    "memory_payload",
    "metrics_payload",
    "personas_payload",
    "session_detail",
    "sessions_payload",
    "runtime_roots",
    "workflow_detail",
    "workflow_runs_dir",
    "workflows_payload",
]
