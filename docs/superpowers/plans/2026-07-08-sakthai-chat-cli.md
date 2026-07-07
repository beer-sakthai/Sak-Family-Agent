# `sakthai chat` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `sakthai chat`, an interactive multi-turn chat command that opens a persistent conversation loop with one of the six Sak Family personas.

**Architecture:** `rich` renders styled, scrolling turn blocks (no alt-screen takeover); `prompt_toolkit` drives the `>` input line. A new `agent/chat.py` module holds the injectable chat loop and renderers; `agent/loop.py` gains a `history` param and `AgentResult.messages` so conversational context threads across turns via one `run_agent()` call per turn. A new `cli/chat.py` wires persona selection (SOUL.md → `system_prompt_prefix`) to that loop.

**Tech Stack:** Python 3.11+, click, `rich`, `prompt_toolkit`, pytest (hermetic, no network/real TTY).

**Spec:** `docs/superpowers/specs/2026-07-07-sakthai-chat-cli-design.md`

## Global Constraints

- New dependencies (`rich`, `prompt_toolkit`) go in `pyproject.toml`'s base `dependencies`, not an extra — `sakthai chat` must work out of the box.
- No per-persona memory isolation: all personas share one `MemoryStore` at `$SAKTHAI_HOME/memory.db`, exactly as `sakthai run` does today.
- No full-screen/curses TUI: styled output must scroll normally (no alt-screen), so the command stays pipeable and testable.
- Tests are hermetic: no network, no real TTY dependency, no real Anthropic/provider credentials. Follow the existing DI convention (`run_agent` takes injectable `client`/`store`; this plan's new code takes injectable `console`/`read_input`).
- `mypy --strict` must stay clean on all new/modified code under `personas/sakthai/sakthai/`.
- `ruff check` and `ruff format --check` must stay clean on the same scope.
- Non-TTY output (piped/redirected) must degrade to plain text — no raw ANSI in redirected output.
- Every `git commit` in this plan stages only the files that task touches (this repo's working tree has unrelated pre-existing modifications from other concurrent work — do not sweep them in with `git add -A`).

---

### Task 1: Add `rich` and `prompt_toolkit` dependencies

**Files:**
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `rich` and `prompt_toolkit` importable from the project's `.venv` for every later task.

- [ ] **Step 1: Add the dependencies**

In `pyproject.toml`, the `dependencies` list currently reads:

```toml
dependencies = [
    "click>=8.4.2,<9.0",
    "pyyaml>=6.0,<7.0",
    "anthropic>=0.116.0,<1.0",
    "httpx>=0.20.0",
    "google-genai>=2.10.0",
    "tenacity>=8.0,<10.0",
    "python-telegram-bot==22.8",
]
```

Change it to:

```toml
dependencies = [
    "click>=8.4.2,<9.0",
    "pyyaml>=6.0,<7.0",
    "anthropic>=0.116.0,<1.0",
    "httpx>=0.20.0",
    "google-genai>=2.10.0",
    "tenacity>=8.0,<10.0",
    "python-telegram-bot==22.8",
    "rich>=13.7,<15.0",
    "prompt-toolkit>=3.0.43,<4.0",
]
```

- [ ] **Step 2: Sync the environment**

Run: `uv sync --all-extras`
Expected: completes with no errors (resolves and installs `rich` and `prompt-toolkit` into `.venv`).

- [ ] **Step 3: Verify the imports**

Run: `uv run python -c "import rich, prompt_toolkit; print('rich', rich.__version__); print('prompt_toolkit', prompt_toolkit.__version__)"`
Expected: prints two version lines, exits 0.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add rich and prompt-toolkit dependencies for sakthai chat"
```

---

### Task 2: Thread conversation history through `run_agent`

**Files:**
- Modify: `personas/sakthai/sakthai/agent/loop.py`
- Test: `tests/test_agent_loop.py`

**Interfaces:**
- Consumes: existing `run_agent(task, *, ..., store=None, client=None, on_event=None, ...)` and `AgentResult(text, iterations, stop_reason, tool_calls=..., usage=...)` (both in `personas/sakthai/sakthai/agent/loop.py`).
- Produces:
  - `run_agent(..., history: Sequence[dict[str, Any]] | None = None, ...) -> AgentResult` — when `history` is given, it seeds the conversation before the new task turn.
  - `AgentResult.messages: list[dict[str, Any]]` — the full transcript *including* the final assistant turn, suitable to pass back in as `history` on the next call.
  - The `tool_call` event payload gains `output_preview: str` (whitespace-collapsed, ≤80 chars) alongside the existing `name`, `input`, `is_error`.

This task has three independent behaviors; each gets its own failing-test-first cycle, then all three are implemented together (they touch overlapping lines in `run_agent`).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_agent_loop.py`. First, add a capturing fake client near the existing `FakeClient` class (it needs to record the exact `messages` payload sent per call, which `FakeClient` doesn't expose):

```python
class _CapturingClient:
    def __init__(self, responses: list) -> None:
        self.received_messages: list[list[dict]] = []
        self._responses = responses
        self._i = 0
        self.messages = self

    def create(self, **kwargs: object) -> _Resp:
        self.received_messages.append(kwargs["messages"])  # type: ignore[arg-type]
        resp = self._responses[self._i]
        self._i += 1
        return resp
```

Then add the three tests (append to the end of the file):

```python
def test_history_seeds_prior_messages(store: MemoryStore) -> None:
    client = _CapturingClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    prior = [
        {"role": "user", "content": "earlier question"},
        {"role": "assistant", "content": [_Block(type="text", text="earlier answer")]},
    ]
    run_agent(
        "follow up",
        client=client,
        store=store,
        provider="anthropic",
        history=prior,
    )
    sent = client.received_messages[0]
    assert sent[0] == prior[0]
    assert sent[1] == prior[1]
    assert sent[2] == {"role": "user", "content": "follow up"}


def test_agent_result_messages_include_final_assistant_turn(store: MemoryStore) -> None:
    block = _Block(type="text", text="hello")
    client = FakeClient([_Resp("end_turn", [block])])
    result = run_agent("hi", client=client, store=store, provider="anthropic")
    assert result.messages[0] == {"role": "user", "content": "hi"}
    assert result.messages[1]["role"] == "assistant"
    assert result.messages[1]["content"] == [block]


def test_tool_call_event_includes_output_preview(store: MemoryStore) -> None:
    events: list[dict[str, Any]] = []
    client = FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="learn", input={"value": "x", "kind": "note"})],
            ),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    run_agent(
        "remember x",
        client=client,
        store=store,
        provider="anthropic",
        on_event=lambda kind, payload: events.append({"kind": kind, **payload}),
    )
    tool_events = [e for e in events if e["kind"] == "tool_call"]
    assert len(tool_events) == 1
    assert tool_events[0]["output_preview"]
    assert len(tool_events[0]["output_preview"]) <= 80
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_agent_loop.py -k "history_seeds or messages_include_final or output_preview" -v`
Expected: 3 FAILs — `history_seeds_prior_messages` fails with `TypeError: run_agent() got an unexpected keyword argument 'history'`; the other two fail on `AttributeError`/`KeyError` for `messages`/`output_preview` not existing yet.

- [ ] **Step 3: Implement — add `messages` to `AgentResult`**

In `personas/sakthai/sakthai/agent/loop.py`, the `AgentResult` dataclass currently ends:

```python
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )
```

Change to:

```python
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, int] = field(
        default_factory=lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    )
    messages: list[dict[str, Any]] = field(default_factory=list)
```

- [ ] **Step 4: Implement — add an output-preview helper**

Just above `def _process_tool_uses(` in the same file, add:

```python
def _preview(text: str, limit: int = 80) -> str:
    """Collapse whitespace and truncate for compact event/log display."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 1] + "…"
```

- [ ] **Step 5: Implement — include the preview in the `tool_call` event**

In `_process_tool_uses`, this line:

```python
        notify("tool_call", {"name": use.name, "input": args, "is_error": is_error})
```

becomes:

```python
        notify(
            "tool_call",
            {
                "name": use.name,
                "input": args,
                "is_error": is_error,
                "output_preview": _preview(output),
            },
        )
```

- [ ] **Step 6: Implement — accept and seed `history`**

`run_agent`'s signature currently has, among its keyword-only params:

```python
    system_prompt_prefix: str = "",
    guardrail_policy: GuardrailPolicy | None = None,
) -> AgentResult:
```

Change to:

```python
    system_prompt_prefix: str = "",
    history: Sequence[dict[str, Any]] | None = None,
    guardrail_policy: GuardrailPolicy | None = None,
) -> AgentResult:
```

Update the docstring's final sentence (`"``client`` and ``store`` are injectable for testing."`) to also mention it:

```python
    ``client`` and ``store`` are injectable for testing. ``history`` seeds the
    conversation with a prior turn's messages (e.g. from a previous
    ``AgentResult.messages``) so multi-turn callers don't lose context.
    """
```

Then, this line:

```python
    messages: list[dict[str, Any]] = [{"role": "user", "content": task}]
```

becomes:

```python
    messages: list[dict[str, Any]] = list(history) if history else []
    messages.append({"role": "user", "content": task})
```

- [ ] **Step 7: Implement — return the final assistant turn in `AgentResult.messages`**

There are two `AgentResult(...)` construction sites inside the `for iteration in ...` loop that return on a terminal/non-tool stop reason. The first:

```python
                result = AgentResult(
                    text=final_text,
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                )
                _save_session_log(task, model, messages, result)
```

becomes:

```python
                result = AgentResult(
                    text=final_text,
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                    messages=[*messages, {"role": "assistant", "content": response.content}],
                )
                _save_session_log(task, model, messages, result)
```

The second (the `stop_reason != "tool_use"` fallback branch):

```python
                result = AgentResult(
                    text=_extract_text(response.content)
                    or f"(unexpected stop_reason={stop_reason!r})",
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                )
                _save_session_log(task, model, messages, result)
```

becomes:

```python
                result = AgentResult(
                    text=_extract_text(response.content)
                    or f"(unexpected stop_reason={stop_reason!r})",
                    iterations=iteration,
                    stop_reason=stop_reason,
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                    messages=[*messages, {"role": "assistant", "content": response.content}],
                )
                _save_session_log(task, model, messages, result)
```

Note `_save_session_log(task, model, messages, result)` is unchanged in both — it keeps logging the pre-append `messages`, matching today's session-log behavior exactly (`result.text` already carries the final text separately in that log).

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_agent_loop.py -v`
Expected: all tests in the file PASS, including the 3 new ones (full file, not just `-k`, to catch any regression in the existing suite from the `messages` list construction change).

- [ ] **Step 9: Type-check and lint**

Run: `uv run mypy personas/sakthai/sakthai/agent/loop.py`
Expected: `Success: no issues found`

Run: `uv run ruff check personas/sakthai/sakthai/agent/loop.py tests/test_agent_loop.py && uv run ruff format --check personas/sakthai/sakthai/agent/loop.py tests/test_agent_loop.py`
Expected: no output, exit 0.

- [ ] **Step 10: Commit**

```bash
git add personas/sakthai/sakthai/agent/loop.py tests/test_agent_loop.py
git commit -m "feat(agent): thread conversation history through run_agent

Adds a history param that seeds prior turns, returns the full
transcript (including the final assistant turn) on AgentResult, and
adds an output_preview to tool_call events. Needed by the upcoming
sakthai chat command so turn N+1 remembers turn N."
```

---

### Task 3: Persona identity resolution

**Files:**
- Modify: `personas/sakthai/sakthai/config.py`
- Create: `personas/sakthai/sakthai/agent/chat.py`
- Test: `tests/test_config_reports.py`
- Test: `tests/test_chat.py` (new)

**Interfaces:**
- Consumes: `config.PERSONAS_DIR` (`personas/sakthai/sakthai/config.py:38`).
- Produces:
  - `config.persona_soul_path(persona: str) -> Path`
  - `config.PERSONA_NAMES: tuple[str, ...]` — the six valid `--persona` values, used by Task 6's CLI option.
  - `agent.chat.load_persona_soul(persona: str) -> str` — SOUL.md contents (stripped), or `""` with a logged warning if missing.
  - `agent.chat.PERSONA_LABELS: dict[str, str]` and `agent.chat.PERSONA_COLORS: dict[str, str]` — used by Task 4's renderers.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_config_reports.py`:

```python
def test_persona_soul_path() -> None:
    assert config.persona_soul_path("sakking") == config.PERSONAS_DIR / "sakking" / "SOUL.md"


def test_persona_names_lists_all_six() -> None:
    assert config.PERSONA_NAMES == (
        "sakking",
        "sakthai",
        "saksee",
        "saksit",
        "saktan",
        "sakjules",
    )
```

Create `tests/test_chat.py`:

```python
"""Tests for sakthai.agent.chat — persona identity, rendering, and the chat loop."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from sakthai import config
from sakthai.agent import chat as chat_agent


def test_load_persona_soul_reads_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persona_dir = tmp_path / "saksee"
    persona_dir.mkdir()
    (persona_dir / "SOUL.md").write_text("  SakSee identity text.  \n", encoding="utf-8")
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)
    assert chat_agent.load_persona_soul("saksee") == "SakSee identity text."


def test_load_persona_soul_missing_file_returns_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)
    with caplog.at_level(logging.WARNING):
        result = chat_agent.load_persona_soul("ghost")
    assert result == ""
    assert "ghost" in caplog.text


def test_persona_labels_and_colors_cover_all_six_personas() -> None:
    assert set(chat_agent.PERSONA_LABELS) == set(config.PERSONA_NAMES)
    assert set(chat_agent.PERSONA_COLORS) == set(config.PERSONA_NAMES)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config_reports.py tests/test_chat.py -v`
Expected: `test_persona_soul_path` and `test_persona_names_lists_all_six` FAIL with `AttributeError: module 'sakthai.config' has no attribute 'persona_soul_path'` (and `'PERSONA_NAMES'`); `tests/test_chat.py` fails to collect with `ModuleNotFoundError: No module named 'sakthai.agent.chat'`.

- [ ] **Step 3: Implement — `config.py`**

In `personas/sakthai/sakthai/config.py`, this line:

```python
PERSONAS_DIR = REPO_ROOT / "personas"
```

becomes:

```python
PERSONAS_DIR = REPO_ROOT / "personas"

# The six Sak Family personas `sakthai chat --persona` can address.
PERSONA_NAMES: tuple[str, ...] = ("sakking", "sakthai", "saksee", "saksit", "saktan", "sakjules")


def persona_soul_path(persona: str) -> Path:
    """Path to a persona's SOUL.md identity file."""
    return PERSONAS_DIR / persona / "SOUL.md"
```

- [ ] **Step 4: Implement — `agent/chat.py`**

Create `personas/sakthai/sakthai/agent/chat.py`:

```python
"""Interactive multi-turn chat: persona identity, rendering, and the REPL loop.

Backs ``sakthai chat``. Keeps `rich`/`prompt_toolkit` I/O at this module's
edges (renderers take an injected ``Console``; the loop takes an injected
``read_input`` callable) so the conversation-flow logic is testable without a
real terminal.
"""

from __future__ import annotations

import logging

from .. import config

logger = logging.getLogger(__name__)

PERSONA_LABELS: dict[str, str] = {
    "sakking": "SakKing",
    "sakthai": "SakThai",
    "saksee": "SakSee",
    "saksit": "SakSit",
    "saktan": "SakTan",
    "sakjules": "SakJules",
}

PERSONA_COLORS: dict[str, str] = {
    "sakking": "bright_magenta",
    "sakthai": "cyan",
    "saksee": "green",
    "saksit": "yellow",
    "saktan": "blue",
    "sakjules": "bright_red",
}


def load_persona_soul(persona: str) -> str:
    """Read a persona's SOUL.md identity text.

    Returns "" (and logs a warning) if the file is unexpectedly missing —
    all six personas currently have one, so this is a defensive fallback,
    not the normal path.
    """
    path = config.persona_soul_path(persona)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        logger.warning(
            "No SOUL.md found for persona %r at %s; using base identity.", persona, path
        )
        return ""
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_config_reports.py tests/test_chat.py -v`
Expected: all PASS.

- [ ] **Step 6: Type-check and lint**

Run: `uv run mypy personas/sakthai/sakthai/config.py personas/sakthai/sakthai/agent/chat.py`
Expected: `Success: no issues found`

Run: `uv run ruff check personas/sakthai/sakthai/config.py personas/sakthai/sakthai/agent/chat.py tests/test_config_reports.py tests/test_chat.py && uv run ruff format --check personas/sakthai/sakthai/config.py personas/sakthai/sakthai/agent/chat.py tests/test_config_reports.py tests/test_chat.py`
Expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
git add personas/sakthai/sakthai/config.py personas/sakthai/sakthai/agent/chat.py tests/test_config_reports.py tests/test_chat.py
git commit -m "feat(agent): resolve persona SOUL.md identity for sakthai chat

Adds config.PERSONA_NAMES/persona_soul_path and a new agent/chat.py
module (load_persona_soul + per-persona label/color maps) that the
chat command will use to load a persona's identity into the system
prompt."
```

---

### Task 4: Rendering helpers

**Files:**
- Modify: `personas/sakthai/sakthai/agent/chat.py`
- Test: `tests/test_chat.py`

**Interfaces:**
- Consumes: `PERSONA_LABELS`, `PERSONA_COLORS` from Task 3; `rich.console.Console`.
- Produces:
  - `render_user_turn(console: Console, text: str) -> None`
  - `make_tool_renderer(console: Console) -> Callable[[str, dict[str, Any]], None]` — an `on_event` callback for `run_agent`.
  - `make_token_renderer(console: Console, persona: str) -> Callable[[str], None]` — an `on_token` callback for `run_agent`.
  - `render_error(console: Console, exc: Exception) -> None`
  - `render_cancelled(console: Console) -> None`
  - `status_line(store: MemoryStore, model: str, tool_count: int) -> str`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_chat.py` (extend the existing imports at the top to add `io`, `Console`, and `MemoryStore`):

```python
import io

from rich.console import Console

from sakthai.memory.store import MemoryStore
```

Then append:

```python
def _console() -> Console:
    return Console(file=io.StringIO(), force_terminal=False, width=100)


def test_render_user_turn_prints_the_text() -> None:
    console = _console()
    chat_agent.render_user_turn(console, "what's in memory?")
    assert "what's in memory?" in console.file.getvalue()  # type: ignore[union-attr]


def test_tool_renderer_prints_name_input_and_output_preview() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event("tool_call", {"name": "recall", "input": {"query": "*"}, "is_error": False, "output_preview": "3 facts found"})
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "recall" in output
    assert "3 facts found" in output


def test_tool_renderer_ignores_non_tool_events() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event("iteration", {"n": 1, "stop_reason": "tool_use"})
    assert console.file.getvalue() == ""  # type: ignore[union-attr]


def test_token_renderer_prints_persona_label_once_then_streams_tokens() -> None:
    console = _console()
    on_token = chat_agent.make_token_renderer(console, "sakking")
    on_token("Hello")
    on_token(" there")
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert output.count("SakKing") == 1
    assert "Hello there" in output


def test_render_error_prints_the_exception_message() -> None:
    console = _console()
    chat_agent.render_error(console, RuntimeError("no credentials"))
    assert "no credentials" in console.file.getvalue()  # type: ignore[union-attr]


def test_render_cancelled_prints_a_marker() -> None:
    console = _console()
    chat_agent.render_cancelled(console)
    assert "cancelled" in console.file.getvalue().lower()  # type: ignore[union-attr]


def test_tool_renderer_emits_no_ansi_codes_when_not_a_terminal() -> None:
    console = _console()
    assert console.is_terminal is False
    on_event = chat_agent.make_tool_renderer(console)
    on_event(
        "tool_call",
        {"name": "recall", "input": {}, "is_error": False, "output_preview": "ok"},
    )
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "\x1b[" not in output


def test_status_line_reports_model_tools_and_fact_count(store: MemoryStore) -> None:
    store.add_fact("v1", kind="note", key="k1")
    line = chat_agent.status_line(store, "claude-opus-4-8", 5)
    assert "claude-opus-4-8" in line
    assert "5 tools" in line
    assert "1 facts" in line
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k "render or status_line or token_renderer" -v`
Expected: FAILs with `AttributeError: module 'sakthai.agent.chat' has no attribute 'render_user_turn'` (and similarly for each missing name).

- [ ] **Step 3: Implement**

Append to `personas/sakthai/sakthai/agent/chat.py` (add `Any`, `Callable` to the `typing`/`collections.abc` imports at the top, and add `from rich.console import Console` and `from ..memory.store import MemoryStore`):

```python
from collections.abc import Callable
from typing import Any

from rich.console import Console

from ..memory.store import MemoryStore
```

Then add:

```python
def render_user_turn(console: Console, text: str) -> None:
    console.print(f"[bold]you[/bold]\n{text}\n")


def make_tool_renderer(console: Console) -> Callable[[str, dict[str, Any]], None]:
    """Build an ``on_event`` callback for ``run_agent`` that renders tool calls."""

    def _on_event(kind: str, payload: dict[str, Any]) -> None:
        if kind != "tool_call":
            return
        tag = "tool!" if payload.get("is_error") else "tool"
        console.print(f"[dim]⚙ {tag} {payload['name']}({payload['input']})[/dim]")
        preview = payload.get("output_preview")
        if preview:
            console.print(f"[dim]  → {preview}[/dim]")

    return _on_event


def make_token_renderer(console: Console, persona: str) -> Callable[[str], None]:
    """Build an ``on_token`` callback for ``run_agent`` that streams a reply.

    Prints the persona's label once, then writes raw token text directly to
    the console's stream (bypassing rich's markup engine) so a stream of
    small deltas doesn't get re-wrapped or re-highlighted mid-word.
    """
    label = PERSONA_LABELS.get(persona, persona)
    color = PERSONA_COLORS.get(persona, "white")
    started = False

    def _on_token(text: str) -> None:
        nonlocal started
        if not started:
            console.print(f"[{color} bold]{label}[/{color} bold]", end=" ")
            started = True
        console.file.write(text)
        console.file.flush()

    return _on_token


def render_error(console: Console, exc: Exception) -> None:
    console.print(f"[red]error:[/red] {exc}")


def render_cancelled(console: Console) -> None:
    console.print("[yellow](cancelled)[/yellow]")


def status_line(store: MemoryStore, model: str, tool_count: int) -> str:
    n_facts = store.stats()["facts"]["total"]
    return f"{model} · {tool_count} tools · memory: {n_facts} facts"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -v`
Expected: all PASS.

- [ ] **Step 5: Type-check and lint**

Run: `uv run mypy personas/sakthai/sakthai/agent/chat.py`
Expected: `Success: no issues found`

Run: `uv run ruff check personas/sakthai/sakthai/agent/chat.py tests/test_chat.py && uv run ruff format --check personas/sakthai/sakthai/agent/chat.py tests/test_chat.py`
Expected: no output, exit 0.

- [ ] **Step 6: Commit**

```bash
git add personas/sakthai/sakthai/agent/chat.py tests/test_chat.py
git commit -m "feat(agent): add rich-based turn/tool/status renderers for sakthai chat"
```

---

### Task 5: The `run_chat` loop

**Files:**
- Modify: `personas/sakthai/sakthai/agent/chat.py`
- Test: `tests/test_chat.py`

**Interfaces:**
- Consumes: `run_agent`, `AgentError`, `AgentResult` (`personas/sakthai/sakthai/agent/loop.py`); `Tool` (`personas/sakthai/sakthai/agent/tools.py`); everything from Tasks 3–4 in this same module.
- Produces: `run_chat(*, persona, soul_text, tools, model, provider, caveman, with_skills, store, console, read_input) -> None` — the interactive loop `cli/chat.py` (Task 6) will call.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_chat.py` (extend imports: add `Callable` — already imported via `collections.abc` from Task 4's production code, but the *test file* needs its own import — add `from collections.abc import Callable` near the top, and `from sakthai.agent.loop import AgentError, AgentResult`):

```python
from collections.abc import Callable

from sakthai.agent.loop import AgentError, AgentResult
```

Then append:

```python
def _make_scripted_input(lines: list[str | None]) -> Callable[[], str | None]:
    it = iter(lines)

    def _read() -> str | None:
        try:
            return next(it)
        except StopIteration:
            return None

    return _read


def test_run_chat_threads_history_across_turns(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    seen_history: list[list[dict[str, Any]]] = []

    def fake_run_agent(task: str, *, history: list[dict[str, Any]] | None = None, **kwargs: Any) -> AgentResult:
        seen_history.append(list(history) if history else [])
        return AgentResult(
            text=f"reply to {task}",
            iterations=1,
            stop_reason="end_turn",
            messages=[
                *(history or []),
                {"role": "user", "content": task},
                {"role": "assistant", "content": f"reply to {task}"},
            ],
        )

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="claude-opus-4-8",
        provider="anthropic",
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["hi", "again", None]),
    )
    assert seen_history[0] == []
    assert seen_history[1][-2] == {"role": "user", "content": "hi"}
    assert seen_history[1][-1] == {"role": "assistant", "content": "reply to hi"}


def test_run_chat_exits_on_slash_exit(monkeypatch: pytest.MonkeyPatch, store: MemoryStore) -> None:
    calls: list[str] = []

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        calls.append(task)
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="m",
        provider=None,
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["hello", "/exit", "should not run"]),
    )
    assert calls == ["hello"]


def test_run_chat_stops_on_eof(monkeypatch: pytest.MonkeyPatch, store: MemoryStore) -> None:
    calls: list[str] = []

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        calls.append(task)
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="m",
        provider=None,
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["hello", None]),
    )
    assert calls == ["hello"]


def test_run_chat_skips_blank_input(monkeypatch: pytest.MonkeyPatch, store: MemoryStore) -> None:
    calls: list[str] = []

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        calls.append(task)
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="m",
        provider=None,
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["   ", "hi", None]),
    )
    assert calls == ["hi"]


def test_run_chat_survives_agent_error(monkeypatch: pytest.MonkeyPatch, store: MemoryStore) -> None:
    calls: list[str] = []

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        calls.append(task)
        if task == "bad":
            raise AgentError("no credentials")
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="m",
        provider=None,
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["bad", "good", None]),
    )
    assert calls == ["bad", "good"]


def test_run_chat_survives_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch, store: MemoryStore) -> None:
    calls: list[str] = []

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        calls.append(task)
        if task == "cancel-me":
            raise KeyboardInterrupt
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="m",
        provider=None,
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["cancel-me", "next", None]),
    )
    assert calls == ["cancel-me", "next"]


def test_run_chat_forwards_persona_and_skills_to_run_agent(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    received: dict[str, Any] = {}

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        received.update(kwargs)
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    chat_agent.run_chat(
        persona="sakking",
        soul_text="SakKing Agent · Runner.",
        tools=(),
        model="claude-opus-4-8",
        provider="anthropic",
        caveman="lite",
        with_skills=("some-skill",),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["hi", None]),
    )
    assert received["system_prompt_prefix"] == "SakKing Agent · Runner."
    assert received["caveman"] == "lite"
    assert received["skills"] == ["some-skill"]
    assert received["store"] is store
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k run_chat -v`
Expected: FAILs with `AttributeError: module 'sakthai.agent.chat' has no attribute 'run_chat'`.

- [ ] **Step 3: Implement**

Append to `personas/sakthai/sakthai/agent/chat.py` (add `from .loop import AgentError, run_agent` and `from .tools import Tool` to the imports at the top):

```python
from .loop import AgentError, run_agent
from .tools import Tool
```

Then add:

```python
def run_chat(
    *,
    persona: str,
    soul_text: str,
    tools: tuple[Tool, ...],
    model: str,
    provider: str | None,
    caveman: str | None,
    with_skills: tuple[str, ...],
    store: MemoryStore,
    console: Console,
    read_input: Callable[[], str | None],
) -> None:
    """Run an interactive chat session: one ``run_agent`` call per turn.

    ``read_input`` returns ``None`` on EOF (Ctrl+D). Typing ``/exit`` ends the
    session the same way. History is carried in-process only via
    ``AgentResult.messages`` — nothing beyond the shared ``MemoryStore`` is
    persisted, so each new ``sakthai chat`` invocation starts a fresh
    transcript (see the design spec's "Memory" section).
    """
    prior_messages: list[dict[str, Any]] = []
    tool_renderer = make_tool_renderer(console)
    while True:
        user_text = read_input()
        if user_text is None or user_text.strip() == "/exit":
            break
        if not user_text.strip():
            continue
        render_user_turn(console, user_text)
        token_renderer = make_token_renderer(console, persona)
        try:
            result = run_agent(
                user_text,
                history=prior_messages,
                system_prompt_prefix=soul_text,
                model=model,
                provider=provider,
                tools=tools,
                caveman=caveman,
                skills=list(with_skills),
                store=store,
                on_event=tool_renderer,
                on_token=token_renderer,
            )
        except AgentError as exc:
            render_error(console, exc)
            continue
        except KeyboardInterrupt:
            render_cancelled(console)
            continue
        console.print()
        prior_messages = result.messages
        console.print(f"[dim]{status_line(store, model, len(tools))}[/dim]\n")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full test suite to catch regressions**

Run: `uv run pytest tests/ -q -m "not integration"`
Expected: all PASS (same count as before this plan started, plus the tests added in Tasks 2–5).

- [ ] **Step 6: Type-check and lint**

Run: `uv run mypy personas/sakthai/sakthai/agent/chat.py`
Expected: `Success: no issues found`

Run: `uv run ruff check personas/sakthai/sakthai/agent/chat.py tests/test_chat.py && uv run ruff format --check personas/sakthai/sakthai/agent/chat.py tests/test_chat.py`
Expected: no output, exit 0.

- [ ] **Step 7: Commit**

```bash
git add personas/sakthai/sakthai/agent/chat.py tests/test_chat.py
git commit -m "feat(agent): add run_chat, the interactive multi-turn REPL loop

One run_agent() call per turn; AgentResult.messages from turn N is
passed back in as history for turn N+1. AgentError and
KeyboardInterrupt are caught per-turn so a bad turn doesn't kill the
session. /exit or EOF ends it."
```

---

### Task 6: `sakthai chat` CLI command

**Files:**
- Create: `personas/sakthai/sakthai/cli/chat.py`
- Modify: `personas/sakthai/sakthai/cli/__init__.py`
- Test: `tests/test_chat.py`

**Interfaces:**
- Consumes: `run_chat`, `load_persona_soul` (`agent/chat.py`, Tasks 3+5); `config.PERSONA_NAMES` (Task 3); `_tool_context` (`personas/sakthai/sakthai/cli/agent.py`); `DEFAULT_MODEL` (`agent/loop.py`).
- Produces: `sakthai chat` command, registered on the root `main` group.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_chat.py` (extend imports: `from click.testing import CliRunner`, `import sakthai.cli.chat as chat_cli`, `from sakthai.cli import main`; also add the `sakthai_home` autouse fixture used by every other CLI test in this repo):

```python
from click.testing import CliRunner

import sakthai.cli.chat as chat_cli
from sakthai.cli import main


@pytest.fixture(autouse=True)
def _isolated_home(sakthai_home: Path) -> Path:
    return sakthai_home


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()
```

Then append:

```python
def test_chat_loads_persona_soul_and_invokes_run_chat(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    persona_dir = tmp_path / "sakking"
    persona_dir.mkdir()
    (persona_dir / "SOUL.md").write_text("SakKing Agent · Runner.", encoding="utf-8")
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)

    calls: list[dict[str, Any]] = []

    def fake_run_chat(**kwargs: Any) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(chat_cli, "run_chat", fake_run_chat)
    monkeypatch.setattr(chat_cli, "_make_read_input", lambda: (lambda: None))

    result = runner.invoke(main, ["chat", "--persona", "sakking", "--no-mcp"])

    assert result.exit_code == 0, result.output
    assert len(calls) == 1
    assert calls[0]["persona"] == "sakking"
    assert calls[0]["soul_text"] == "SakKing Agent · Runner."
    assert calls[0]["with_skills"] == ()


def test_chat_defaults_to_sakthai_persona(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    persona_dir = tmp_path / "sakthai"
    persona_dir.mkdir()
    (persona_dir / "SOUL.md").write_text("SakThai identity.", encoding="utf-8")
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)

    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(chat_cli, "run_chat", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(chat_cli, "_make_read_input", lambda: (lambda: None))

    result = runner.invoke(main, ["chat", "--no-mcp"])

    assert result.exit_code == 0, result.output
    assert calls[0]["persona"] == "sakthai"


def test_chat_rejects_invalid_persona(runner: CliRunner) -> None:
    result = runner.invoke(main, ["chat", "--persona", "notreal", "--no-mcp"])
    assert result.exit_code != 0
    assert "notreal" in result.output


def test_chat_forwards_model_provider_caveman_and_skills(
    runner: CliRunner, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    persona_dir = tmp_path / "sakthai"
    persona_dir.mkdir()
    (persona_dir / "SOUL.md").write_text("id", encoding="utf-8")
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)

    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(chat_cli, "run_chat", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(chat_cli, "_make_read_input", lambda: (lambda: None))

    result = runner.invoke(
        main,
        [
            "chat",
            "--no-mcp",
            "--model",
            "gpt-4o",
            "--provider",
            "openai",
            "--caveman",
            "lite",
            "--with-skills",
            "skill-a",
            "--with-skills",
            "skill-b",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls[0]["model"] == "gpt-4o"
    assert calls[0]["provider"] == "openai"
    assert calls[0]["caveman"] == "lite"
    assert calls[0]["with_skills"] == ("skill-a", "skill-b")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k test_chat_ -v`
Expected: FAILs — `ModuleNotFoundError: No module named 'sakthai.cli.chat'`, and (once that's created but before registration) `Error: No such command 'chat'`.

- [ ] **Step 3: Implement — `cli/chat.py`**

Create `personas/sakthai/sakthai/cli/chat.py`:

```python
"""The ``chat`` command: an interactive multi-turn REPL with a Sak Family persona."""

from __future__ import annotations

from collections.abc import Callable

import click
from rich.console import Console

from .. import config
from ..agent.chat import load_persona_soul, run_chat
from ..agent.loop import DEFAULT_MODEL
from ..memory.store import MemoryStore
from .agent import _tool_context


def _make_read_input() -> Callable[[], str | None]:
    from prompt_toolkit import PromptSession

    session: PromptSession[str] = PromptSession()

    def _read() -> str | None:
        try:
            return session.prompt("> ")
        except EOFError:
            return None

    return _read


@click.command()
@click.option(
    "--persona",
    type=click.Choice(config.PERSONA_NAMES),
    default="sakthai",
    show_default=True,
    help="Which Sak Family persona to chat with.",
)
@click.option("--model", default=DEFAULT_MODEL, show_default=True, help="Model identifier.")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["anthropic", "google", "openai", "ollama", "gateway"]),
    help="LLM provider backend.",
)
@click.option(
    "--no-mcp",
    is_flag=True,
    help="Don't load external MCP servers (from ~/.sakthai/mcp.json and extensions).",
)
@click.option(
    "--with-skills",
    "with_skills",
    multiple=True,
    help="Inject the named skill's instructions into the system prompt (repeatable).",
)
@click.option(
    "--caveman",
    type=click.Choice(["lite", "full", "ultra", "wenyan-lite", "wenyan-full", "wenyan-ultra"]),
    help="Enable Caveman token compression at the specified intensity level.",
)
def chat(
    persona: str,
    model: str,
    provider: str | None,
    no_mcp: bool,
    with_skills: tuple[str, ...],
    caveman: str | None,
) -> None:
    """Open an interactive multi-turn chat session with a Sak Family persona.

    Type /exit or press Ctrl+D to end the session. Conversation history is
    kept in-process for this session only; continuity across separate
    `sakthai chat` runs comes from persistent memory, same as `sakthai run`.
    """
    soul_text = load_persona_soul(persona)
    console = Console()
    store = MemoryStore()
    try:
        with _tool_context(no_mcp=no_mcp, verbose=False) as tools:
            run_chat(
                persona=persona,
                soul_text=soul_text,
                tools=tools,
                model=model,
                provider=provider,
                caveman=caveman,
                with_skills=with_skills,
                store=store,
                console=console,
                read_input=_make_read_input(),
            )
    finally:
        store.close()
```

- [ ] **Step 4: Implement — register the command**

In `personas/sakthai/sakthai/cli/__init__.py`, this import line:

```python
from .agent import mcp, run
```

becomes:

```python
from .agent import mcp, run
from .chat import chat
```

And this line:

```python
main.add_command(run)
main.add_command(mcp)
```

becomes:

```python
main.add_command(run)
main.add_command(mcp)
main.add_command(chat)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -v`
Expected: all PASS.

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest tests/ -q -m "not integration"`
Expected: all PASS.

- [ ] **Step 7: Manual smoke check**

Run: `uv run sakthai chat --help`
Expected: prints usage help listing `--persona`, `--model`, `--provider`, `--no-mcp`, `--with-skills`, `--caveman`, with `sakking|sakthai|saksee|saksit|saktan|sakjules` as the `--persona` choices.

Run: `uv run sakthai --help`
Expected: `chat` appears in the command list alongside `run`, `mcp`, etc.

- [ ] **Step 8: Type-check and lint**

Run: `uv run mypy personas/sakthai/sakthai/cli/chat.py personas/sakthai/sakthai/cli/__init__.py`
Expected: `Success: no issues found`

Run: `uv run ruff check personas/sakthai/sakthai/cli/chat.py personas/sakthai/sakthai/cli/__init__.py tests/test_chat.py && uv run ruff format --check personas/sakthai/sakthai/cli/chat.py personas/sakthai/sakthai/cli/__init__.py tests/test_chat.py`
Expected: no output, exit 0.

- [ ] **Step 9: Commit**

```bash
git add personas/sakthai/sakthai/cli/chat.py personas/sakthai/sakthai/cli/__init__.py tests/test_chat.py
git commit -m "feat(cli): add sakthai chat command

Wires persona selection (SOUL.md -> system_prompt_prefix), the shared
tool context (BUILTIN_TOOLS + optional MCP servers), and a real
prompt_toolkit input source into the run_chat loop from agent/chat.py.
Completes the first sakthai-chat-cli-design.md spec."
```

---

## Plan-level verification (after all 6 tasks)

- [ ] Run the full gate this repo's CI runs: `uv run ruff check personas/sakthai/sakthai tests && uv run ruff format --check personas/sakthai/sakthai tests && uv run mypy personas/sakthai/sakthai && uv run pytest tests/ -q -m "not integration"`
  Expected: all four commands succeed with no errors.
- [ ] `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai`
  Expected: no new high/medium findings introduced by `cli/chat.py` or `agent/chat.py`.
- [ ] Manually run `uv run sakthai chat --persona sakking --dry-run` — wait, `--dry-run` isn't a chat option (by design, see spec's Non-goals). Instead: confirm `ANTHROPIC_API_KEY` (or `claude login`) is set, then run `uv run sakthai chat --persona sakking`, send one message, confirm a styled reply streams in with the "SakKing Agent · ..." label, then type `/exit` and confirm it returns to the shell cleanly.
