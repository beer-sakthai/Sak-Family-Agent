# `sakthai chat` — Interactive Multi-Turn Chat CLI — Design

**Status:** Approved, ready for implementation planning
**Scope:** First of two specs toward "personas at Claude-Code-level capability."
This spec covers the interactive chat CLI only. A second spec (tool-capability
upgrades — file editing, glob/grep search, todo tracking, and possibly wiring
the existing `agent-self-evolution` DSPy/GEPA pipeline) is out of scope here
and will be brainstormed separately.

## Goal

Today, `sakthai run "<task>"` is one-shot: it takes a single task string, runs
the agent loop to completion, and exits. There is no way to have a live,
multi-turn conversation with a persona from the terminal — every follow-up
requires a new `sakthai run` invocation that starts from a blank slate (no
awareness of what was just discussed, beyond whatever facts happen to be in
persistent memory).

This spec adds `sakthai chat`, a new interactive command that opens a
persistent conversation loop with one of the six Sak Family personas
(SakKing, SakThai, SakSee, SakSit, SakTan, SakJules), styled and structured
close to the real `claude` CLI's chat experience: colored, formatted turns,
visible tool-call activity, streaming replies, and a proper input line with
history.

## Non-goals (out of scope for this spec)

- Resumable/saved conversation transcripts across separate `sakthai chat`
  invocations (`claude --continue`-style). Each launch starts a fresh
  transcript; continuity across launches is via the existing shared
  `MemoryStore`, not a new session-persistence mechanism.
- Per-persona memory isolation. All personas continue to share one
  `MemoryStore`, matching the personas' own stated identity ("we share a
  unified long-term memory, though we maintain separate active sessions" —
  `personas/sakking/SOUL.md` and siblings).
- `--sandbox`, `--dry-run`, `--fast`, `--stateless` inside chat — these don't
  fit a persistent interactive session and are dropped from the chat command's
  flag set (they remain available on `sakthai run`).
- A full-screen (Textual/curses-style) TUI with a persistent redrawn border.
  See "Rejected approach" below.
- Expanding the built-in tool set (file editing, glob/grep, todo tracking).
  That is the second, separate spec referenced above.
- Wiring the `agent-self-evolution` (DSPy/GEPA) pipeline into this command.

## Approach

### Rejected approach: full-screen TUI (Textual)

A `textual`-based full-screen app (persistent bordered frame, fixed input bar,
live-redrawn on resize) was considered and would most closely match a mockup
the user approved during brainstorming. Rejected for v1 because: it requires
a new async event loop wrapping the existing synchronous `run_agent()`
tool-dispatch flow, only works against a real TTY (breaks this repo's
hermetic, pipeable test conventions), and is substantially more code to build
and debug than the value it adds over styled scrolling output. Revisit if
user feedback on the v1 chat command specifically calls out the missing
persistent frame.

### Chosen approach: `rich` for rendering + `prompt_toolkit` for input

Turns print as styled blocks that scroll normally in the terminal (no
alt-screen takeover) using `rich.Console`; the `>` input prompt uses
`prompt_toolkit` for line history and multi-line input editing. This gets
the substantive visual/UX value (color, structure, tool-call panels, persona
identity, input history) without a rewrite of the agent loop's execution
model, and keeps the command scriptable (pipeable stdin/stdout, works in
tests and non-interactive shells).

New base dependencies (not extras-gated — `sakthai chat` should work out of
the box): `rich`, `prompt_toolkit`.

## Design

### 1. Command surface

New file `personas/sakthai/sakthai/cli/chat.py`, registered in
`cli/__init__.py` alongside the other command groups.

```
sakthai chat [OPTIONS]

--persona {sakking,sakthai,saksee,saksit,saktan,sakjules}  (default: sakthai)
--model TEXT
--provider {anthropic,google,openai,ollama,gateway}
--no-mcp
--with-skills TEXT   (repeatable)
--caveman {lite,full,ultra,wenyan-lite,wenyan-full,wenyan-ultra}
```

Flags mirror `sakthai run` where they make sense for a persistent session.
Dropped: `--stream` (streaming is always-on for chat), `--dry-run`, `--fast`,
`--stateless`, `--sandbox` (see Non-goals).

### 2. Persona resolution

`--persona <name>` resolves to `PERSONAS_DIR / <name> / "SOUL.md"` (using the
existing `config.PERSONAS_DIR`). Its contents are read and passed as
`run_agent(..., system_prompt_prefix=soul_text)` — the same mechanism the
Telegram bots already use via `SAKTHAI_SYSTEM_PROMPT_FILE` /
`sakthai_system_prompt_prefix()`, just invoked directly here instead of
through an env var. If the file is unexpectedly missing (defensive only — all
six personas currently have one), fall back to no prefix (base `SYSTEM_BASE`
identity) and print a one-line warning to stderr; do not crash.

Each persona gets a static display color for its reply blocks (six colors,
one per persona, defined as a constant map in `cli/chat.py`).

### 3. Memory

No new mechanism. `run_agent()` is called with the default (shared)
`MemoryStore` at `$SAKTHAI_HOME/memory.db`, exactly as `sakthai run` does
today. This is intentional: it matches the personas' documented shared-memory
identity, and it's what gives continuity across separate `sakthai chat`
launches without building session persistence.

### 4. Conversation history within a session

**Supporting change to `agent/loop.py`** (required — without it, each turn
would forget the previous turn's conversational content the instant it ends,
leaving only whatever got explicitly saved via `learn`):

- `run_agent()` gains an optional keyword param `history: list[dict] | None
  = None`. When provided, it seeds the internal `messages` list instead of
  always starting from `[{"role": "user", "content": task}]`.
- `AgentResult` gains a `messages: list[dict[str, Any]]` field carrying the
  full updated transcript for that call, so the caller can pass it back in
  as `history` on the next call.

**New module** `personas/sakthai/sakthai/agent/chat.py` — the interactive
loop itself, injectable for testing (see Testing section):

```python
def run_chat(
    *,
    persona: str,
    soul_text: str,
    tools: tuple[Tool, ...],
    model: str,
    provider: str | None,
    caveman: str | None,
    console: Console,              # rich.Console, injectable
    read_input: Callable[[], str | None],  # returns None on EOF/exit
) -> None:
    prior_messages: list[dict[str, Any]] = []
    while True:
        user_text = read_input()
        if user_text is None:
            break
        render_user_turn(console, user_text)
        try:
            result = run_agent(
                user_text,
                history=prior_messages,
                system_prompt_prefix=soul_text,
                model=model, provider=provider, tools=tools, caveman=caveman,
                on_event=make_tool_renderer(console, persona),
                on_token=make_token_renderer(console, persona),
            )
        except AgentError as exc:
            render_error(console, exc)
            continue
        except KeyboardInterrupt:
            render_cancelled(console)
            continue
        prior_messages = result.messages
```

One `run_agent()` call per turn. The growing `messages` list is the only
state carried between calls — no separate history store, nothing persisted
to disk beyond what `MemoryStore` already persists (matches the "fresh each
launch" decision).

### 5. Tool-call event payload

The existing `tool_call` event (`_process_tool_uses` in `agent/loop.py`)
carries `{name, input, is_error}` but not the tool's output, so a result line
like `→ 3 facts found` can't be rendered from it today. Small addition: include
a truncated (~80 char) preview of the tool result string in the payload:
`{name, input, is_error, output_preview}`.

### 6. Rendering

- **Turn blocks**: `you` in a neutral style; tool calls as dim single-line
  panels (`⚙ tool_name({args})` then `→ <output_preview>` once the result
  lands); persona replies prefixed with that persona's self-identification
  line pulled from its SOUL.md (e.g. "SakKing Agent · Runner, Email, Message
  & General Assistant."), colored per the persona color map.
- **Streaming**: `on_token` feeds `rich.Console` incrementally (same
  mechanism as today's `--stream` on `sakthai run`), so replies appear as
  they're generated rather than all at once.
- **Status line**: one-line footer after each turn — `model · N tools ·
  memory: N facts` — refreshed via a cheap `MemoryStore` count.
- **Exit**: Ctrl+D (EOF) or typing `/exit` ends the session cleanly.
- **Cancel**: Ctrl+C during a turn is caught around the single `run_agent()`
  call, cancels just that turn, and returns to the prompt — it does not kill
  the process or lose prior turns.
- **Non-TTY / piped input**: gate styling on `console.is_terminal`; when
  false (piped, redirected, CI), degrade to plain text so the command stays
  scriptable and doesn't emit raw ANSI into redirected output.

### 7. Testing

Following this repo's existing DI convention (`run_agent` already takes
injectable `client`/`store`; tests never touch real credentials or a real
DB):

- `run_chat()` takes an injectable `read_input` callable and `console`
  (constructed in non-terminal mode for tests), so tests drive a scripted
  conversation (a list of canned inputs, ending in `None`) with `run_agent`
  mocked exactly like `tests/test_agent_loop.py` already does, and assert on
  what gets passed into each `run_agent` call (in particular, that `history`
  on turn 2 contains turn 1's assistant/tool messages) and on rendered
  output.
- `agent/loop.py`: unit tests that `history` seeds `messages` correctly,
  that `AgentResult.messages` is populated, and that the `tool_call` event
  payload carries `output_preview`.
- `cli/chat.py`: persona → SOUL.md resolution for all six valid persona
  names; an invalid `--persona` value is rejected by Click before any agent
  call happens.
- Ctrl+C mid-turn does not crash `run_chat`'s loop (simulate by having the
  mocked `run_agent` raise `KeyboardInterrupt`).
- Non-TTY mode suppresses `rich` styling (assert on `console.is_terminal`
  gating, not on literal ANSI byte sequences).

## Dependencies

Add to `pyproject.toml` base dependencies: `rich`, `prompt_toolkit`.

## Files touched (implementation-time reference)

- `personas/sakthai/sakthai/cli/chat.py` — new
- `personas/sakthai/sakthai/cli/__init__.py` — register `chat` command
- `personas/sakthai/sakthai/agent/chat.py` — new (chat loop + renderers)
- `personas/sakthai/sakthai/agent/loop.py` — add `history` param,
  `AgentResult.messages`, `output_preview` in `tool_call` event payload
- `pyproject.toml` — add `rich`, `prompt_toolkit`
- `tests/test_agent_loop.py` — history/messages/event-payload coverage
- `tests/test_chat.py` — new, chat loop + CLI coverage
