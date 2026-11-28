# Tool-call live running state — design spec

Date: 2026-07-25

## Context

Beer wants `sakthai-chat-cli`'s tool-call transparency to approach the level
of Claude Code, Gemini CLI, and GitHub Copilot CLI. That's three independent
subsystems, decomposed into separate specs:

1. **Live running state** (this spec) — a tool call becomes visible the
   instant it starts, not only after it finishes.
2. Permission prompts for risky tools (e.g. `run_command`) — separate spec,
   not yet designed.
3. Expandable/collapsible long tool output — separate spec, not yet designed.

Today, `make_tool_renderer`'s `_on_event` callback (`sakthai/agent/chat.py:135-162`)
only reacts to a single `"tool_call"` event, fired once — *after* the tool
has already run — from `_process_tool_uses` in `sakthai/agent/loop.py:258-300`
(the `notify("tool_call", {...})` call at line 283, which happens after
`_execute_tool_with_guardrails` on line 281 has already returned). There is
currently no signal that a tool call has *started*; for a slow tool (a shell
command, a large file read), the terminal shows nothing until it's done.

## Goal

The moment a tool call begins, print a visible "running" indicator. When it
finishes, print the existing result line, now annotated with elapsed time.

## Design

### 1. New event: `tool_call_start`

In `sakthai/agent/loop.py`, `_process_tool_uses` (around line 280), add one
call immediately *before* `_execute_tool_with_guardrails` runs:

```python
notify("tool_call_start", {"name": use.name, "input": args})
```

The existing `notify("tool_call", {...})` call after execution is
unchanged — same event name, same payload shape. This is purely additive:
any consumer that only branches on `kind == "tool_call"` (both
`sakthai/agent/chat.py:148` and `sakthai/cli/agent.py:57`) silently ignores
the new `"tool_call_start"` kind and keeps working exactly as today. No
existing test or call site breaks.

Tool calls are processed one at a time in `_process_tool_uses`'s `for use in
tool_uses:` loop — never concurrently — so a single "currently running"
piece of state is sufficient on the rendering side; no need to track
multiple in-flight calls by ID.

### 2. Rendering — `make_tool_renderer` in `sakthai/agent/chat.py`

Track one `start_time: float | None` in the closure (alongside the existing
`accent` variable). On `tool_call_start`:

- Record `start_time = time.perf_counter()`.
- Print a dim "running" line reusing the existing glyph/name/truncated-args
  formatting: `⚙ {name}({truncated args}) …`

On `tool_call` (the existing end event), after computing the elapsed time
from the recorded `start_time`:

- Print the result line exactly as today (name, args, error marker, result
  preview), with elapsed time appended using the same format `status_bar`
  already uses elsewhere (`sakthai/agent/ui.py:283-285`:
  `f"⏱ {elapsed:.1f}s"`), e.g. `⚙ read_file(...) ✓ ⏱ 0.3s`.

This produces two lines per tool call (running, then done) rather than
updating one line in place — deliberately avoiding a `Live` region for this
feature (see "Approaches not taken" below).

### 3. Non-terminal fallback

`make_tool_renderer` currently has no non-terminal-specific branch (unlike
`ReplyStream`, which special-cases non-terminal consoles). The existing
`"tool_call"` line print already works unconditionally via
`console.print(...)`, which is safe for both terminal and non-terminal
(piped) output. The new "running" line follows the same unconditional
`console.print(...)` pattern — no new fallback logic needed.

## Approaches not taken

- **In-place `Live`-updating line** (running line morphs into the done
  line): visually tighter, but requires wiring a `Live` context through the
  tool renderer and re-deriving the non-terminal fallback `ReplyStream`
  already had to build. Two static lines is simpler and sufficient.
- **Merging into the existing thinking spinner** (`ReplyStream.start_thinking`):
  would unify spinner → tool activity → reply panel into one continuous
  `Live` region, but couples `make_tool_renderer` and `ReplyStream`, which
  are currently independent `on_event`/`on_token` callbacks passed
  separately to `run_agent`. Out of scope for "just event timing."

## Testing

- `tests/test_agent_loop.py`, alongside the existing
  `test_tool_call_event_includes_output_preview` (line 2114), which already
  exercises `_process_tool_uses`'s `notify` calls: add a test that captures
  the full sequence of `(kind, payload)` calls and asserts `"tool_call_start"`
  precedes `"tool_call"` for the same tool name, and that the
  `"tool_call_start"` payload is exactly `{"name": ..., "input": ...}` (no
  `output_preview`/`is_error` keys yet, since the tool hasn't run).
- `tests/test_chat.py`: extend the existing tool-renderer tests
  (`test_tool_renderer_prints_name_input_and_output_preview` and
  neighbors, around line 83) with a case that fires `tool_call_start` then
  `tool_call` through `make_tool_renderer`'s returned callback, asserting:
  the running line appears before the done line, and the done line
  contains an elapsed-time marker (e.g. `"⏱"` in the output).
- A test firing only `tool_call_start` with no follow-up `tool_call` (e.g.
  simulating a tool that never returns) is not required — no cleanup logic
  depends on that event pair being complete; each print is independent and
  stateless beyond the single `start_time` variable used to compute the
  *next* elapsed duration.

## Out of scope

- Permission prompts and expandable/collapsible output — separate specs
  (subsystems 2 and 3 above).
- Distinct per-tool-type running copy (e.g. "reading file.py…" vs generic
  "⚙ read_file(...) …") — YAGNI for this pass; the generic trace format
  matches what the renderer already does for the done line.
- Concurrent/parallel tool call tracking — the current agent loop executes
  tool calls strictly sequentially; no design is needed for overlapping
  in-flight calls.
