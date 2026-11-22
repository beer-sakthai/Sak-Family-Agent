# Tool-Call Live Running State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A tool call becomes visible in the chat REPL the instant it starts, not only after it finishes, with elapsed time shown once it completes.

**Architecture:** A new `tool_call_start` event fires in the agent loop immediately before a tool executes (purely additive alongside the existing post-execution `tool_call` event). The chat renderer tracks one in-flight start time and prints a "running" line on start, then appends elapsed time to the existing result line on completion.

**Tech Stack:** Python 3.11+, `time.perf_counter()`, Rich `Text`/`Console`, pytest.

## Global Constraints

- This is purely additive: the existing `"tool_call"` event's name and payload shape do not change. Any consumer that only branches on `kind == "tool_call"` (`sakthai/agent/chat.py:148`, `sakthai/cli/agent.py:57`) must keep working unchanged with zero edits.
- Tool calls execute strictly sequentially (never concurrently) — one `start_time` variable is sufficient, no per-call ID tracking (spec section 1).
- Elapsed time uses the exact format already used by `status_bar` (`sakthai/agent/ui.py:283-285`): `f"⏱ {elapsed:.1f}s"`.
- No `Live` region, no new dependency (spec "Approaches not taken").
- Lint (`ruff check sakthai tests`), format check (`ruff format --check sakthai tests`), type-check (`mypy sakthai`), and `bandit -c pyproject.toml -r sakthai` must all stay green.

---

### Task 1: `tool_call_start` event in the agent loop

**Files:**
- Modify: `sakthai/agent/loop.py:266-291` (`_process_tool_uses`)
- Test: `tests/test_agent_loop.py` (append near `test_tool_call_event_includes_output_preview`, line 2114)

**Interfaces:**
- Produces: a `notify("tool_call_start", {"name": str, "input": dict[str, Any]})` call, fired before `notify("tool_call", {...})` for the same tool invocation. Task 2 consumes this event kind by name only (no new function signature) — it reads `kind == "tool_call_start"` in `make_tool_renderer`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_agent_loop.py`, directly after `test_tool_call_event_includes_output_preview` (after line 2135):

```python
def test_tool_call_start_event_fires_before_tool_call_with_no_extra_keys(
    store: MemoryStore,
) -> None:
    events: list[dict[str, Any]] = []
    client = FakeClient(
        [
            _Resp(
                "tool_use",
                [
                    _Block(
                        type="tool_use", id="t1", name="learn", input={"value": "x", "kind": "note"}
                    )
                ],
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
    kinds = [e["kind"] for e in events]
    start_index = kinds.index("tool_call_start")
    end_index = kinds.index("tool_call")
    assert start_index < end_index
    assert events[start_index] == {
        "kind": "tool_call_start",
        "name": "learn",
        "input": {"value": "x", "kind": "note"},
    }
```

This reuses the `_Block`, `_Resp`, `FakeClient`, and `run_agent` fixtures already imported/defined at the top of `tests/test_agent_loop.py` (no new imports needed).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agent_loop.py::test_tool_call_start_event_fires_before_tool_call_with_no_extra_keys -v`
Expected: FAIL with `ValueError: 'tool_call_start' is not in list` (the `kinds.index("tool_call_start")` call)

- [ ] **Step 3: Write the implementation**

In `sakthai/agent/loop.py`, in `_process_tool_uses`, insert one line before `_execute_tool_with_guardrails` is called:

```python
        args = dict(use.input or {})
        notify("tool_call_start", {"name": use.name, "input": args})
        output, is_error = _execute_tool_with_guardrails(tool, args, store, policy)
```

(This replaces the existing two-line block `args = dict(use.input or {})` /
`output, is_error = _execute_tool_with_guardrails(tool, args, store, policy)`
at lines 280-281 — everything else in `_process_tool_uses` is unchanged,
including the `notify("tool_call", {...})` call that follows.)

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agent_loop.py::test_tool_call_start_event_fires_before_tool_call_with_no_extra_keys -v`
Expected: PASS

- [ ] **Step 5: Run the full test suite, lint, and type-check**

Run: `uv run pytest tests/ -q && uv run ruff check sakthai tests && uv run mypy sakthai`
Expected: all pass (aside from any pre-existing unrelated failures already present on this branch — do not fix those, just confirm this change adds none)

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/loop.py tests/test_agent_loop.py
git commit -m "feat: fire tool_call_start event before tool execution"
```

---

### Task 2: Render the running line and elapsed time

**Files:**
- Modify: `sakthai/agent/chat.py:135-162` (`make_tool_renderer`)
- Test: `tests/test_chat.py` (append near `test_tool_renderer_prints_name_input_and_output_preview`, line 83)

**Interfaces:**
- Consumes: the `"tool_call_start"` event kind (Task 1) — by string name only; this task does not import anything new from Task 1.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_chat.py`, directly after `test_tool_renderer_prints_name_input_and_output_preview` (after line 97):

```python
def test_tool_renderer_prints_a_running_line_on_tool_call_start() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event("tool_call_start", {"name": "recall", "input": {"query": "*"}})
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "recall" in output


def test_tool_renderer_running_line_appears_before_the_done_line_with_elapsed() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event("tool_call_start", {"name": "recall", "input": {"query": "*"}})
    on_event(
        "tool_call",
        {
            "name": "recall",
            "input": {"query": "*"},
            "is_error": False,
            "output_preview": "3 facts found",
        },
    )
    lines = [
        line
        for line in console.file.getvalue().splitlines()  # type: ignore[union-attr]
        if "recall" in line
    ]
    assert len(lines) == 2
    assert "⏱" not in lines[0]
    assert "⏱" in lines[1]


def test_tool_renderer_without_a_start_event_omits_elapsed_time() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event(
        "tool_call",
        {
            "name": "recall",
            "input": {"query": "*"},
            "is_error": False,
            "output_preview": "3 facts found",
        },
    )
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "⏱" not in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k "running_line or without_a_start_event" -v`
Expected: FAIL — `test_tool_renderer_prints_a_running_line_on_tool_call_start` fails because
`on_event("tool_call_start", ...)` currently returns immediately (the `if kind != "tool_call": return` guard), printing nothing, so `"recall" in output` is `False`.

- [ ] **Step 3: Write the implementation**

Replace `make_tool_renderer` (lines 135-162) in `sakthai/agent/chat.py`:

```python
def make_tool_renderer(
    console: Console, persona: str | None = None
) -> Callable[[str, dict[str, Any]], None]:
    """Build an ``on_event`` callback for ``run_agent`` that renders tool calls.

    On ``tool_call_start`` prints a dim "running" trace line immediately.
    On ``tool_call`` (the existing post-execution event) prints the result —
    glyph and tool name in the persona's accent color, arguments dimmed,
    elapsed time appended — with the result preview indented beneath it, so
    tool activity reads as a distinct layer between the user and reply panels.
    """
    accent = PERSONA_ACCENTS.get(persona or "", "cyan")
    start_time: float | None = None

    def _on_event(kind: str, payload: dict[str, Any]) -> None:
        nonlocal start_time
        if kind == "tool_call_start":
            start_time = time.perf_counter()
            line = Text()
            line.append(f"{GLYPH_TOOL} {payload['name']}", style=f"bold {accent}")
            line.append(_truncate(f"({payload['input']})"), style="dim")
            line.append(" …", style="dim")
            console.print(line)
            return
        if kind != "tool_call":
            return
        elapsed = time.perf_counter() - start_time if start_time is not None else None
        start_time = None
        line = Text()
        line.append(f"{GLYPH_TOOL} {payload['name']}", style=f"bold {accent}")
        line.append(_truncate(f"({payload['input']})"), style="dim")
        if payload.get("is_error"):
            line.append(f" {GLYPH_ERROR}", style="bold red")
        if elapsed is not None:
            line.append(f" ⏱ {elapsed:.1f}s", style="dim")
        console.print(line)
        preview = payload.get("output_preview")
        if preview:
            result = Text(f"  {GLYPH_RESULT} ", style=accent)
            result.append(str(preview), style="dim italic")
            console.print(result)

    return _on_event
```

`time` is already imported at the top of `sakthai/agent/chat.py` (line 12,
`import time`) — no new import needed.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -k "tool_renderer" -v`
Expected: PASS (all tool-renderer tests, including the 3 new ones and the pre-existing `test_tool_renderer_prints_name_input_and_output_preview` / `test_tool_renderer_ignores_non_tool_events` / `test_tool_renderer_truncates_long_input` / `test_tool_renderer_marks_errors` / `test_tool_renderer_emits_no_ansi_codes_when_not_a_terminal`)

- [ ] **Step 5: Run the full test suite, lint, format check, type-check, and security scan**

Run: `uv run pytest tests/ -q && uv run ruff check sakthai tests && uv run ruff format --check sakthai tests && uv run mypy sakthai && uv run bandit -c pyproject.toml -r sakthai`
Expected: all pass (aside from any pre-existing unrelated failures already present on this branch)

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/chat.py tests/test_chat.py
git commit -m "feat: show a running line and elapsed time for tool calls"
```

---

## Self-Review Notes

- **Spec coverage:** Spec section 1 (new event) → Task 1. Spec section 2 (rendering) → Task 2. Spec section 3 (non-terminal fallback) is satisfied by construction — Task 2's new `console.print(line)` call for the running line uses the exact same unconditional-print pattern the existing done-line print already uses, no separate fallback branch needed, matching the spec's explicit statement that no new fallback logic is required. Testing section requirements are covered by Task 1's and Task 2's test steps exactly as specified (same test file locations, same assertions).
- **Placeholder scan:** none — every step has complete, exact code.
- **Type consistency:** `notify`'s signature (`Callable[[str, dict[str, Any]], None]`) is unchanged across both tasks; Task 2's `_on_event` keeps the exact same `Callable[[str, dict[str, Any]], None]` return type `make_tool_renderer` already declares. `start_time: float | None` is scoped entirely within Task 2, never crosses a task boundary.
