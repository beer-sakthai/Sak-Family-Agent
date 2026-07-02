# Phase 4 Memory Architecture & Session Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-session content search (CLI + agent tool) to the Sak-Family-Agent, per the approved spec at `docs/superpowers/specs/2026-07-02-phase4-memory-session-search-design.md`, without changing `MemoryStore`'s schema.

**Architecture:** A single new module, `sakthai/memory/session_search.py`, owns the on-demand scan over `~/.sakthai/sessions/*.json` and exposes one function, `search_sessions()`. Both the CLI subcommand (`sakthai sessions search`) and the new agent tool (`search_sessions` in `BUILTIN_TOOLS`) call this one function — no duplicated scan logic. Session files are read, not written; the feature is inherently read-only/idempotent.

**Tech Stack:** Python 3.11, Click (CLI), stdlib `json`/`pathlib`/`dataclasses`, pytest (TDD), mypy strict, ruff, bandit, uv.

## Global Constraints

- Python 3.11 target (`pyproject.toml` `[tool.ruff] target-version = "py311"`, `[tool.mypy] python_version = "3.11"`).
- `mypy strict = true` over `sakthai/` — every new function needs full type annotations.
- Ruff: line-length 100, rule set `["E", "F", "W", "I", "UP", "B", "SIM"]` (E501 and SIM108 ignored). No unused-argument rule is enabled, so an intentionally-unused `store: MemoryStore` tool-handler parameter is fine as-is (matches existing handlers' signature requirement).
- Coverage floor 85% (`fail_under = 85`) over `sakthai/` — new code needs tests, not just happy-path.
- Tests are hermetic: no network, no real `~/.sakthai`. Use the existing `sakthai_home` fixture (`tests/conftest.py`) to sandbox `SAKTHAI_HOME`, and `tmp_path` directly when a function accepts an injectable directory.
- Commit message style: short imperative subject line, no strict Conventional Commits prefix enforced but this repository's recent history uses `feat:`/`fix:`/`docs:`/`test:` prefixes — follow that.
- Per this repository's workflow: local `uv run pytest`, `ruff check`, `ruff format --check`, `mypy`, `bandit` must all be green before pushing; push, wait for green CI, then merge (not just a local commit).

---

### Task 1: Cycle checkpoint — Dream → Hope

**Files:** none (this task only runs `sakthai` CLI commands against the local memory store; no repository files change).

**Interfaces:**
- Consumes: nothing.
- Produces: nothing importable — this task's effect is state in `~/.sakthai/memory.db` (the persisted cycle stage and two new facts), used only as a process checkpoint, not by later tasks' code.

- [ ] **Step 1: Confirm current cycle stage**

Run: `uv run sakthai cycle status`
Expected: `Stage 1/6  [DREAM]  Define the vision or task` (if a prior session already advanced the stage, note the actual output instead of failing the task on this step).

- [ ] **Step 2: Recall prior context (Dream stage guidance)**

Run: `uv run sakthai memory show`
Expected: prints the current facts/observations table (may be empty on a fresh `~/.sakthai`); this is a recall step, not a check for specific content.

- [ ] **Step 3: Advance to Hope and record the key design decisions**

Run:
```bash
uv run sakthai cycle next
uv run sakthai learn "Phase 4 session search: AND-of-terms query over task/result.text/result.tool_calls, no MemoryStore schema change, on-demand file scan (not FTS5), no new SAKTHAI_*_ALLOW gating (search_sessions is not a new privilege — sessions show already exposes the same data by ID)." --kind decision --key phase4-session-search
```
Expected: `cycle next` prints `Stage 2/6  [HOPE]  Engineer a solution`; `learn` prints `Stored fact id=<N> (kind=decision, key=phase4-session-search).`

---

### Task 2: `search_sessions()` core module

**Files:**
- Create: `sakthai/memory/session_search.py`
- Test: `tests/test_session_search.py`

**Interfaces:**
- Consumes: `sakthai.config.sessions_dir() -> Path` (existing).
- Produces (for Tasks 3 and 4):
  - `sakthai.memory.session_search.SessionMatch` — frozen dataclass with fields `session_id: str`, `timestamp: float | None`, `task: str`, `matched_snippet: str`.
  - `sakthai.memory.session_search.search_sessions(query: str, limit: int = 20, sessions_dir: Path | None = None) -> list[SessionMatch]` — raises `ValueError` if `query` is empty/whitespace-only; returns `[]` if the sessions directory doesn't exist; results sorted by `timestamp` descending.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_session_search.py`:

```python
"""Tests for cross-session content search."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.memory.session_search import SessionMatch, search_sessions


def _write_session(
    directory: Path,
    session_id: str,
    *,
    timestamp: int,
    task: str = "",
    result_text: str = "",
    tool_calls: list[dict] | None = None,
) -> None:
    payload = {
        "timestamp": timestamp,
        "task": task,
        "model": "claude-opus-4-8",
        "usage": {"total_tokens": 0},
        "result": {
            "text": result_text,
            "iterations": 1,
            "stop_reason": "end_turn",
            "tool_calls": tool_calls or [],
        },
        "messages": [],
    }
    (directory / f"{session_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_matches_on_task_text(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="Explain quantum physics")
    _write_session(tmp_path, "s2", timestamp=200, task="Bake a cake")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_matches_on_result_text(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="task", result_text="The answer is 42.")

    results = search_sessions("answer", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_matches_on_tool_call_name_and_input(tmp_path: Path) -> None:
    _write_session(
        tmp_path,
        "s1",
        timestamp=100,
        task="task",
        tool_calls=[{"name": "learn", "input": {"value": "uses vim"}, "is_error": False}],
    )

    by_name = search_sessions("learn", sessions_dir=tmp_path)
    by_input = search_sessions("vim", sessions_dir=tmp_path)

    assert [m.session_id for m in by_name] == ["s1"]
    assert [m.session_id for m in by_input] == ["s1"]


def test_and_of_terms_requires_all_terms(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="quantum physics lecture")
    _write_session(tmp_path, "s2", timestamp=200, task="quantum computing")

    results = search_sessions("quantum physics", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_no_match_returns_empty_list(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="bake a cake")

    assert search_sessions("quantum", sessions_dir=tmp_path) == []


def test_case_insensitive_matching(tmp_path: Path) -> None:
    _write_session(tmp_path, "s1", timestamp=100, task="Explain QUANTUM Physics")

    results = search_sessions("quantum physics", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_empty_query_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        search_sessions("", sessions_dir=tmp_path)


def test_whitespace_only_query_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        search_sessions("   ", sessions_dir=tmp_path)


def test_missing_sessions_directory_returns_empty_list(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    assert search_sessions("anything", sessions_dir=missing) == []


def test_corrupt_session_file_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{not valid json", encoding="utf-8")
    _write_session(tmp_path, "s1", timestamp=100, task="quantum physics")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["s1"]


def test_results_ordered_by_timestamp_descending(tmp_path: Path) -> None:
    _write_session(tmp_path, "oldest", timestamp=100, task="quantum")
    _write_session(tmp_path, "newest", timestamp=300, task="quantum")
    _write_session(tmp_path, "middle", timestamp=200, task="quantum")

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert [m.session_id for m in results] == ["newest", "middle", "oldest"]


def test_limit_caps_result_count(tmp_path: Path) -> None:
    for i in range(5):
        _write_session(tmp_path, f"s{i}", timestamp=100 + i, task="quantum")

    results = search_sessions("quantum", sessions_dir=tmp_path, limit=2)

    assert len(results) == 2


def test_matched_snippet_contains_query_context(tmp_path: Path) -> None:
    _write_session(
        tmp_path,
        "s1",
        timestamp=100,
        task="A long task description that mentions quantum physics somewhere in the middle",
    )

    results = search_sessions("quantum", sessions_dir=tmp_path)

    assert "quantum" in results[0].matched_snippet.lower()


def test_session_match_is_frozen_dataclass() -> None:
    match = SessionMatch(session_id="s1", timestamp=100.0, task="t", matched_snippet="snip")
    with pytest.raises(AttributeError):
        match.session_id = "s2"  # type: ignore[misc]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_session_search.py -v`
Expected: `ModuleNotFoundError: No module named 'sakthai.memory.session_search'` (all tests error, not just fail).

- [ ] **Step 3: Write the implementation**

Create `sakthai/memory/session_search.py`:

```python
"""Search across past agent session logs by content."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import sessions_dir as default_sessions_dir

_SNIPPET_RADIUS = 40  # characters of context kept on each side of a match


@dataclass(frozen=True)
class SessionMatch:
    session_id: str
    timestamp: float | None
    task: str
    matched_snippet: str


def _searchable_text(data: dict[str, Any]) -> str:
    """Flatten the fields worth searching out of a session payload.

    Deliberately does not walk ``messages[]``: ``result.tool_calls`` is
    already a flat ``list[dict]`` with the same names/inputs, so there is
    no need to parse the nested transcript blocks.
    """
    parts: list[str] = []
    task = data.get("task")
    if isinstance(task, str):
        parts.append(task)
    result = data.get("result") or {}
    text = result.get("text")
    if isinstance(text, str):
        parts.append(text)
    for call in result.get("tool_calls") or []:
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        if isinstance(name, str):
            parts.append(name)
        tool_input = call.get("input")
        if tool_input:
            parts.append(json.dumps(tool_input, ensure_ascii=False))
    return "\n".join(parts)


def _snippet(haystack: str, term: str) -> str:
    lower = haystack.lower()
    idx = lower.find(term.lower())
    if idx == -1:
        return haystack[:80]
    start = max(0, idx - _SNIPPET_RADIUS)
    end = min(len(haystack), idx + len(term) + _SNIPPET_RADIUS)
    snippet = haystack[start:end].replace("\n", " ").strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(haystack) else ""
    return f"{prefix}{snippet}{suffix}"


def search_sessions(
    query: str,
    limit: int = 20,
    sessions_dir: Path | None = None,
) -> list[SessionMatch]:
    """Search session logs for sessions whose content matches every term in ``query``.

    Matching is case-insensitive AND-of-terms over the session's task, final
    answer text, and tool-call names/inputs. Corrupt or unreadable session
    files are skipped. Results are ordered by session timestamp, most recent
    first.
    """
    if not query or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")
    terms = query.strip().lower().split()

    dir_path = sessions_dir if sessions_dir is not None else default_sessions_dir()
    if not dir_path.exists():
        return []

    matches: list[SessionMatch] = []
    for path in dir_path.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        haystack = _searchable_text(data)
        lower = haystack.lower()
        if not all(term in lower for term in terms):
            continue
        matches.append(
            SessionMatch(
                session_id=path.stem,
                timestamp=data.get("timestamp"),
                task=data.get("task", ""),
                matched_snippet=_snippet(haystack, terms[0]),
            )
        )

    matches.sort(key=lambda m: m.timestamp or 0, reverse=True)
    return matches[:limit]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_session_search.py -v`
Expected: all 14 tests `PASSED`.

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy sakthai/memory/session_search.py && uv run ruff check sakthai/memory/session_search.py tests/test_session_search.py`
Expected: `Success: no issues found` from mypy; no output (clean) from ruff.

- [ ] **Step 6: Commit**

```bash
git add sakthai/memory/session_search.py tests/test_session_search.py
git commit -m "feat: add search_sessions() for cross-session content search"
```

---

### Task 3: `sakthai sessions search` CLI command

**Files:**
- Modify: `sakthai/cli/sessions.py`
- Test: `tests/test_sessions_cli.py`

**Interfaces:**
- Consumes: `search_sessions(query, limit, sessions_dir=None) -> list[SessionMatch]` and `SessionMatch` from Task 2 (`sakthai.memory.session_search`).
- Produces: the `sakthai sessions search <query> [--limit N]` CLI command (no importable interface — verified via `CliRunner`, as the existing `sessions list`/`show`/`clean` commands are).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_sessions_cli.py` (append at the end of the file):

```python
def test_sessions_search_finds_match(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    sess_id = f"{now}_quantum-sess"
    payload = {
        "timestamp": now,
        "task": "Explain quantum physics",
        "model": "claude-opus-4-8",
        "usage": {"total_tokens": 10},
        "result": {"text": "done", "iterations": 1, "stop_reason": "end_turn", "tool_calls": []},
        "messages": [],
    }
    (s_dir / f"{sess_id}.json").write_text(json.dumps(payload), encoding="utf-8")

    res = runner.invoke(main, ["sessions", "search", "quantum"])
    assert res.exit_code == 0
    assert sess_id in res.output


def test_sessions_search_no_matches(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["sessions", "search", "nonexistent-term"])
    assert res.exit_code == 0
    assert "No matching sessions found." in res.output


def test_sessions_search_empty_query_reports_error(sakthai_home: Path, runner: CliRunner) -> None:
    res = runner.invoke(main, ["sessions", "search", ""])
    assert res.exit_code != 0
    assert "`query` is required" in res.output


def test_sessions_search_respects_limit(sakthai_home: Path, runner: CliRunner) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    for i in range(5):
        payload = {
            "timestamp": now - i,
            "task": "quantum topic",
            "result": {"text": "", "iterations": 1, "stop_reason": "end_turn", "tool_calls": []},
            "messages": [],
        }
        (s_dir / f"{now - i}_sess-{i}.json").write_text(json.dumps(payload), encoding="utf-8")

    res = runner.invoke(main, ["sessions", "search", "quantum", "--limit", "2"])
    assert res.exit_code == 0
    match_lines = [line for line in res.output.splitlines() if "_sess-" in line]
    assert len(match_lines) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_sessions_cli.py -k search -v`
Expected: `Error: No such command 'search'.` (all 4 new tests fail).

- [ ] **Step 3: Write the implementation**

In `sakthai/cli/sessions.py`, add the import alongside the existing `from ..config import sessions_dir` line:

```python
from ..memory.session_search import search_sessions
```

Then add this command after `sessions_show` (before `sessions_clean`):

```python
@sessions.command("search")
@click.argument("query")
@click.option("--limit", default=20, show_default=True, help="Maximum sessions to show.")
def sessions_search(query: str, limit: int) -> None:
    """Search past sessions by content (task, final answer, and tool calls)."""
    try:
        matches = search_sessions(query, limit=limit)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if not matches:
        click.echo("No matching sessions found.")
        return

    click.secho(f"{'Session ID':<45} {'Date/Time':<19} {'Snippet':<70}", bold=True)
    click.echo("-" * 140)
    for m in matches:
        dt_str = ""
        if m.timestamp:
            dt_str = datetime.fromtimestamp(m.timestamp, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"{m.session_id:<45} {dt_str:<19} {m.matched_snippet:<70}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_sessions_cli.py -v`
Expected: all tests in the file `PASSED` (existing `sessions list`/`show`/`clean` tests plus the 4 new `search` tests).

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy sakthai/cli/sessions.py && uv run ruff check sakthai/cli/sessions.py tests/test_sessions_cli.py`
Expected: `Success: no issues found` from mypy; no output from ruff.

- [ ] **Step 6: Commit**

```bash
git add sakthai/cli/sessions.py tests/test_sessions_cli.py
git commit -m "feat: add sakthai sessions search CLI command"
```

---

### Task 4: `search_sessions` agent tool

**Files:**
- Modify: `sakthai/agent/tools.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Consumes: `search_sessions(query, limit, sessions_dir=None) -> list[SessionMatch]` from Task 2 (`sakthai.memory.session_search`); `_coerce_limit(raw: Any, default: int) -> int` (existing, in this same file).
- Produces: a new `Tool` named `"search_sessions"` in `BUILTIN_TOOLS`, automatically available to both `sakthai run` (agent loop) and `sakthai mcp` (MCP server) — no other wiring needed, per this repository's existing tool-registry pattern.

- [ ] **Step 1: Write the failing tests**

Add this import alongside the existing `from sakthai.memory.store import MemoryStore` line at
the top of `tests/test_tools.py`:

```python
from sakthai.config import sessions_dir
```

Then add to `tests/test_tools.py` (append at the end of the file):

```python
def test_search_sessions_tool_finds_and_filters(sakthai_home: Path, store: MemoryStore) -> None:
    s_dir = sessions_dir()
    s_dir.mkdir(parents=True, exist_ok=True)
    (s_dir / "100_quantum.json").write_text(
        json.dumps(
            {
                "timestamp": 100,
                "task": "Explain quantum physics",
                "result": {"text": "", "tool_calls": []},
            }
        ),
        encoding="utf-8",
    )
    (s_dir / "200_cake.json").write_text(
        json.dumps(
            {"timestamp": 200, "task": "Bake a cake", "result": {"text": "", "tool_calls": []}}
        ),
        encoding="utf-8",
    )

    out = tool_by_name("search_sessions").handler({"query": "quantum"}, store)

    assert "quantum" in out.lower()
    assert "cake" not in out.lower()


def test_search_sessions_tool_no_matches(sakthai_home: Path, store: MemoryStore) -> None:
    out = tool_by_name("search_sessions").handler({"query": "nonexistent"}, store)
    assert "No matching sessions found" in out


def test_search_sessions_tool_requires_query(sakthai_home: Path, store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        tool_by_name("search_sessions").handler({"query": "  "}, store)
```

Note: `sakthai_home` (sandboxes `SAKTHAI_HOME`) is required here alongside `store` (an independent in-memory-backed `MemoryStore`) because the tool handler calls `search_sessions()` with no explicit `sessions_dir`, so it resolves the real `config.sessions_dir()` — which must point at the sandboxed `SAKTHAI_HOME`, not the developer's real `~/.sakthai`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tools.py -k search_sessions -v`
Expected: `AttributeError: 'NoneType' object has no attribute 'handler'` (`tool_by_name("search_sessions")` returns `None` — the tool doesn't exist yet).

- [ ] **Step 3: Write the implementation**

In `sakthai/agent/tools.py`, add the import alongside the existing `from ..memory.store import MemoryStore` line:

```python
from ..memory.session_search import search_sessions as search_past_sessions
```

Add this handler function after `_search` (before `_forget`):

```python
def _search_sessions(args: dict[str, Any], store: MemoryStore) -> str:
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("`query` is required and must be a non-empty string.")
    limit = _coerce_limit(args.get("limit"), 20)
    matches = search_past_sessions(query, limit=limit)
    if not matches:
        return f"No matching sessions found for '{query}'."
    lines = [f"Matching Sessions ({len(matches)}):"]
    lines.extend(f"  {m.session_id}  {m.task}  — {m.matched_snippet}" for m in matches)
    return "\n".join(lines)
```

Add this `Tool` entry in `BUILTIN_TOOLS`, immediately after the `"search"` tool block (before the `"forget"` tool block):

```python
    Tool(
        name="search_sessions",
        description=(
            "Search past agent session logs by content (task, final answer, and tool "
            "calls). Use to find what was done or discussed in a prior session, as "
            "opposed to `search`, which searches stored facts/observations."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Whitespace-separated search terms; all must match.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum sessions to return.",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
        handler=_search_sessions,
    ),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py -v`
Expected: all tests in the file `PASSED`, including `test_registry_names_unique_and_schemas_valid` (which iterates all of `BUILTIN_TOOLS`, so it exercises the new entry's schema automatically) and the 3 new `search_sessions` tests.

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy sakthai/agent/tools.py && uv run ruff check sakthai/agent/tools.py tests/test_tools.py`
Expected: `Success: no issues found` from mypy; no output from ruff.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/tools.py tests/test_tools.py
git commit -m "feat: expose search_sessions as a built-in agent/MCP tool"
```

---

### Task 5: Add the Phase 4 checklist to `product/todo.md`

**Files:**
- Modify: `product/todo.md`

**Interfaces:** none — documentation only.

- [ ] **Step 1: Add the Phase 4 section**

In `product/todo.md`, add a new section after the existing `## Phase 3: Hermes-free runtime migration` section (i.e. at the end of the file), matching the `[x]`/checklist style of Phases 1–3:

```markdown
## Phase 4: Memory architecture and session search

- [ ] **Architecture audit:**
  - Documented in `docs/superpowers/specs/2026-07-02-phase4-memory-session-search-design.md`.
  - Confirms `MemoryStore`'s schema is unchanged by this phase; the gap is a missing search
    surface over session logs, which live outside the store entirely.

- [ ] **`search_sessions()`:**
  - Implemented in `sakthai/memory/session_search.py`.
  - AND-of-terms, case-insensitive query over task/result.text/result.tool_calls.
  - On-demand scan (no persistent index), timestamp-descending order.

- [ ] **CLI command:**
  - `sakthai sessions search <query> [--limit N]` in `sakthai/cli/sessions.py`.

- [ ] **Agent tool:**
  - `search_sessions` added to `BUILTIN_TOOLS`; reachable from both `sakthai run` and `sakthai mcp`.

- [ ] **Test coverage:**
  - `tests/test_session_search.py`, plus extensions to `tests/test_tools.py` and
    `tests/test_sessions_cli.py`.

- [ ] **Local verification:**
  - `uv run pytest tests/test_session_search.py tests/test_tools.py tests/test_sessions_cli.py -q`
    passing, plus a manual `sakthai sessions search` smoke run.

- [ ] **GitHub delivery:**
  - Committed, pushed, PR opened, merged after green CI.
```

- [ ] **Step 2: Commit**

```bash
git add product/todo.md
git commit -m "docs: add Phase 4 checklist to product/todo.md"
```

---

### Task 6: Full verification suite + Cycle Care/Trust checkpoint

**Files:** none (verification only; the Phase 4 checklist items in `product/todo.md` get checked off here, see Step 5).

**Interfaces:** none.

- [ ] **Step 1: Run the full local check sequence**

Run: `uv run ruff check sakthai tests && uv run ruff format --check sakthai tests && uv run mypy sakthai && uv run bandit -c pyproject.toml -r sakthai && uv run pytest -m "not integration" -q`
Expected: every command exits 0; pytest reports all tests passing with no new failures (existing suite + the ~20 tests added across Tasks 2–4).

If `ruff format --check` fails, run `uv run ruff format sakthai tests`, review the diff, then re-run the full sequence.

- [ ] **Step 2: Record the Care-stage finding**

Run:
```bash
uv run sakthai cycle next
uv run sakthai learn "Phase 4 Care check: ruff/mypy/bandit/pytest all green for session_search.py, cli/sessions.py search command, and the search_sessions tool. No concurrency concerns — search_sessions() is a pure read over immutable session files, no locking needed." --kind finding --key phase4-care-check
```
Expected: `cycle next` prints `Stage 3/6  [CARE]  Refine quality — concurrency and performance`; `learn` confirms the fact was stored.

- [ ] **Step 3: Manual smoke test**

Run:
```bash
uv run sakthai sessions search quantum
uv run sakthai sessions search ""
```
Expected: first command runs without a traceback (prints either matches from your real `~/.sakthai/sessions` or "No matching sessions found."); second command exits non-zero with an error message containing `` `query` is required ``.

- [ ] **Step 4: Advance to Joy and check memory stats**

Run:
```bash
uv run sakthai cycle next
uv run sakthai memory stats
```
Expected: `cycle next` prints `Stage 4/6  [JOY]  Package and ship`; `memory stats` prints without error.

- [ ] **Step 5: Advance to Trust and run doctor**

Run:
```bash
uv run sakthai cycle next
uv run sakthai doctor
```
Expected: `cycle next` prints `Stage 5/6  [TRUST]  Secure the foundation`; `doctor` reports no new failures relative to a pre-Phase-4 baseline run (pre-existing unrelated warnings, e.g. missing optional API keys, are not blockers for this phase).

- [ ] **Step 6: Check off the Phase 4 items in `product/todo.md`**

Edit `product/todo.md`: change every `- [ ]` added in Task 5 to `- [x] YYYY-MM-DD` (using today's actual date), for the items verified in Steps 1–5 above (Architecture audit, `search_sessions()`, CLI command, Agent tool, Test coverage, Local verification). Leave **GitHub delivery** as `- [ ]` — that is checked off in Task 7, after the PR is actually merged.

- [ ] **Step 7: Commit**

```bash
git add product/todo.md
git commit -m "docs: check off Phase 4 items verified locally"
```

---

### Task 7: Push, green CI, merge, Cycle Growth checkpoint

**Files:**
- Modify: `product/todo.md` (final checkbox only)

**Interfaces:** none.

- [ ] **Step 1: Push the branch**

Run: `git push -u origin <branch-name>` (or `git push` if already tracking a remote branch).
Expected: push succeeds.

- [ ] **Step 2: Open a PR and wait for CI**

Run: `gh pr create --title "Phase 4: memory architecture and session search" --body "Implements docs/superpowers/specs/2026-07-02-phase4-memory-session-search-design.md — adds search_sessions() (memory/session_search.py), the sakthai sessions search CLI command, and the search_sessions agent/MCP tool. No MemoryStore schema changes."`
Then watch CI (`gh pr checks --watch` or the repository's GitHub Actions UI) until every required check (secret-scan, lint, format-check, mypy, bandit, pytest across Python 3.11/3.12/3.13, smoke-test) is green.

- [ ] **Step 3: Merge**

Run: `gh pr merge --squash` (or the repository's usual merge method) once all checks are green.
Expected: PR merges into `main`.

- [ ] **Step 4: Cycle Growth checkpoint**

Run:
```bash
uv run sakthai cycle next
uv run sakthai memory consolidate
uv run sakthai cycle next
```
Expected: first `cycle next` prints `Stage 6/6  [GROWTH]  Learn and grow`; `memory consolidate` runs without error; second `cycle next` wraps back around to `Stage 1/6  [DREAM]  Define the vision or task`, closing the loop per this repository's `CLAUDE.md` Principle 3 ("a cycle isn't done until Trust has signed off and Growth has fed the lesson back into memory").

- [ ] **Step 5: Check off GitHub delivery and commit**

Edit `product/todo.md`: change the Phase 4 **GitHub delivery** item from `- [ ]` to `- [x] YYYY-MM-DD` (today's date).

```bash
git add product/todo.md
git commit -m "docs: mark Phase 4 GitHub delivery complete"
git push
```
