# Design: Full-screen Textual TUI for `sakthai chat`

**Date:** 2026-07-26
**Status:** Approved (design), pending implementation plan
**Author:** Beer + SakThai (Claude)

## Problem

Today `sakthai chat` interleaves a `prompt_toolkit` input line with `rich`
console output. Both print inline to the terminal scrollback, so each turn
prints the input, then the reply *below* it — the conversation marches **down**
the screen and the compose line is never in a fixed place.

Beer wants a Claude-Code-style layout: the message input **pinned at the bottom
of the screen**, with the conversation scrolling **up** above it.

## Decision (from brainstorming)

- **Target UX:** a **full-screen Textual TUI** (alternate-screen app) with a
  scrollable conversation pane above a fixed bottom input. (Chosen over the
  "sticky input, keep scrollback" prompt_toolkit option.)
- **Rollout:** **replace the current chat UI entirely.** There is no `--plain`
  fallback and no `--tui` flag. `sakthai chat` always launches the TUI.
- **Feature parity:** everything the current chat does must survive v1
  (streaming + markdown, tool-call traces, slash commands + completion +
  history, persona look + status bar).
- **Chosen approach:** **Approach A** — a Textual app that *reuses the existing
  `sakthai/agent/ui.py` Rich renderables* (panels, chips, banners) by mounting
  them into Textual widgets, rather than rebuilding every message as a native
  Textual widget from scratch.

### Accepted trade-offs

- `sakthai chat` becomes **TTY-only**. Piped/redirected/non-terminal invocation
  will error out (Textual requires a terminal). The non-interactive path is
  `sakthai run`, which is unchanged. This is acceptable because chat is
  inherently interactive.
- The existing rich-inline chat tests (which asserted on `Console` output) are
  **replaced** by Textual `Pilot` tests plus unit tests for the extracted
  renderable builders. The 85% branch-coverage floor still applies.

## Architecture

One new module, plus a refactor of the existing chat module into pure builders
and an app that drives them.

### Components

1. **`sakthai/agent/tui.py` — `SakThaiApp(textual.app.App)`** (new)
   The full-screen application. Owns layout, key bindings, slash-command
   dispatch, and the turn lifecycle. Holds session state: `prior_messages`,
   `goal`, `persona`, `model`, `provider`, `tools`, `store`, `soul_text`,
   `caveman`, `with_skills`.

   **Layout (compose):**
   - A top `Static` welcome/banner region (reuses `ui.welcome_panel`).
   - A `VerticalScroll` **conversation pane** (`#conversation`) that
     auto-scrolls to the bottom as widgets are mounted into it.
   - A bottom bar: the persona-colored `Input` (`#compose`) plus a status /
     shortcut `Static` strip (reuses `ui.status_bar` and the shortcut hints
     currently in the prompt_toolkit `bottom_toolbar`).

2. **Message widgets** (lightweight `Static` subclasses or plain `Static`s
   holding Rich renderables):
   - **User turn** — `ui`-built user panel (extracted from
     `chat.render_user_turn`).
   - **Tool trace** — one `Static` per tool call, built from the same
     `Text` currently produced in `chat.make_tool_renderer`.
   - **Reply** — a single updatable widget per turn: shows the thinking
     spinner, then the accumulating streamed text, then is updated to the final
     Markdown panel on completion. Backed by the `ReplyStream` accumulation
     logic (refactored to expose "current renderable" instead of driving a
     `rich.Live`).

3. **`sakthai/agent/chat.py` — refactor to pure builders** (existing)
   Extract renderable construction so both any legacy callers and the TUI use
   one source of truth:
   - `user_panel(text) -> Panel` (from `render_user_turn`).
   - Reply panel construction (`ReplyStream._panel`) exposed as a builder the
     app can call for streaming and final states.
   - Tool-trace line construction exposed as a builder.
   - `handle_slash_command` refactored to be side-effect-free: instead of
     calling `console.print(...)`, it returns
     `(handled: bool, goal: str | None, renderables: list[RenderableType])`.
     The app mounts each returned renderable into `#conversation`. The panels it
     returns (`help_panel`, `tools_panel`, `memory_panel`, `skills_panel`)
     already exist in `ui.py` and are reused unchanged.
   - `run_chat` (the old rich/prompt_toolkit REPL loop) is **removed**.

4. **`sakthai/cli/chat.py` — wiring** (existing)
   Replace `_make_read_input` / `run_chat(...)` with
   `SakThaiApp(persona=..., ...).run()`. Remove the `prompt_toolkit` imports,
   `_prompt_style`, `_bottom_toolbar`, `_slash_completer`, `_make_read_input`.
   The Click command, options, and `_tool_context` usage are unchanged.

### Data flow (one turn)

```
Input.submit
  -> app.on_input_submitted(text)
     -> slash command?  yes -> dispatch, mount reused ui.* panel, return
                        no  -> continue
     -> mount user_panel(text) into #conversation
     -> match_persona(text) -> mount best-matched chip on the reply widget
     -> mount reply widget in "thinking" (spinner) state
     -> run_worker(_run_turn, thread=True)         # off the UI thread
          _run_turn calls run_agent(
              text, history=prior_messages, ...,
              on_token=..., on_event=...)
            on_token(delta)  -> app.call_from_thread(reply.append, delta)
            on_event(kind,p) -> app.call_from_thread(app.mount_tool_trace, p)
          on success -> app.call_from_thread(reply.finalize_markdown, ...)
                        + update prior_messages + mount status_bar
          on AgentError / KeyboardInterrupt (cancel) ->
                        call_from_thread(render error / cancelled)
```

Threading rule: `run_agent` is synchronous and network-bound, so it runs in a
Textual **worker thread**. All widget mutation from that thread goes through
`App.call_from_thread(...)` (or posted messages) so it happens on the UI thread.
Nothing else in the agent/memory layer changes.

### Feature parity mapping

| Current feature | TUI realization |
|---|---|
| Streaming reply + final markdown | Reply widget: spinner -> streamed `Text` -> `Markdown` panel on `finalize`. |
| Thinking spinner | Reply widget's initial state (Rich `Spinner` in a `Static`, or Textual `LoadingIndicator`). |
| Tool-call traces | One `Static` per `tool_call` event mounted between user panel and reply. |
| Slash commands `/help /tools /skills /memory /clear /goal /exit` | Handled in `on_input_submitted`; reuse `ui.*_panel` builders; `/clear` empties `#conversation` + resets `prior_messages`; `/exit` -> `app.exit()`. |
| Tab-completion of slash commands | Textual `Input(suggester=...)` with a custom `Suggester` that suggests from `SLASH_COMMANDS` when the text starts with `/`. Bind Tab/Right to accept. |
| History + auto-suggest | Same `Suggester` also suggests from `~/.sakthai/chat_history`; Up/Down browse history. History file reused (same path as today). |
| Welcome banner / persona colors / avatars | `ui.welcome_panel`, `theme.PERSONA_*` reused verbatim; persona color applied to `Input` border via CSS set at mount. |
| Best-matched-persona chip | `ui.chip(...)` mounted onto/above the reply widget, as today. |
| Per-turn status bar | A **persistent bottom footer** `Static` rebuilt from `ui.status_bar(...)` after each completed turn (model, tool count, facts, elapsed, goal). |
| Ctrl-C cancel / Ctrl-D quit | Key bindings: Ctrl-C cancels the running worker (mirrors current `KeyboardInterrupt` handling); Ctrl-D / `/exit` quits. |

### Dependencies

- **Add** `textual` (MIT, free) to `pyproject.toml` runtime deps.
- **Remove** `prompt_toolkit` (only used by the chat path:
  `cli/chat.py`, `agent/chat.py`, and `PERSONA_PROMPT_COLORS` in `theme.py`).
  Drop the now-unused `PERSONA_PROMPT_COLORS` if nothing else references it.
- **Dev:** add `pytest-asyncio` if not present (Textual `run_test()` is async);
  optionally `pytest-textual-snapshot` for snapshot tests (evaluate, not
  required for v1).

### Error handling

- `AgentError` -> mount an error `Static` (reuse `chat.render_error` styling as a
  builder) and leave the input ready for the next turn.
- Worker cancellation (Ctrl-C mid-turn) -> mount the "cancelled" line, keep the
  session alive.
- Non-TTY launch -> Textual raises on `run()`; catch it in `cli/chat.py` and
  print a one-line message telling the user chat requires a terminal and to use
  `sakthai run` for non-interactive use. (Exit non-zero.)

### Testing

- **Renderable builders** (extracted from `chat.py`): plain unit tests, no
  terminal — assert the returned `Panel`/`Text` structure/plain text. These
  carry most of the coverage cheaply.
- **App behavior** via `async with SakThaiApp(...).run_test() as pilot:` —
  - type text + Enter -> a user panel and a reply widget appear;
  - a mocked provider streams tokens -> reply text grows then finalizes;
  - a mocked tool event -> a trace widget mounts;
  - each slash command mounts the right panel / clears / exits;
  - the agent is injected/mocked at the same provider boundary the current
    tests use (hermetic: no network, no credentials).
- Keep everything `@pytest.mark.integration`-free; maintain the 85% branch floor
  (`fail_under` in `pyproject.toml`).

## Out of scope (v1, YAGNI)

- Mouse selection / copy affordances beyond Textual defaults.
- Multiline compose editor, message editing, resend.
- Scrollback persistence across sessions (history of *messages*); only the
  input `chat_history` file persists, as today.
- Snapshot-image regression tests (may add later).
- Any change to `sakthai run`, the MCP server, memory, providers, or tools.
