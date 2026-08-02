# Chat Textual TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the inline `prompt_toolkit`/`rich` chat REPL with a full-screen Textual TUI whose input is pinned at the bottom and whose conversation scrolls up above it.

**Architecture:** A new `SakThaiApp(textual.app.App)` composes a `VerticalScroll` conversation pane above a fixed `Input`. It reuses the existing `sakthai/agent/ui.py` Rich renderables (panels, chips, banners) by mounting them into Textual `Static` widgets (Approach A). `run_agent` runs in a Textual worker thread; its `on_token`/`on_event` callbacks marshal UI updates back with `App.call_from_thread`.

**Tech Stack:** Python 3.12, Textual, Rich, Click, pytest + pytest-asyncio (Textual `run_test()` / `Pilot`).

## Global Constraints

- Chat is **TTY-only**; non-terminal launch must fail with a clear message pointing to `sakthai run`. `sakthai run`, MCP, memory, providers, tools are unchanged.
- **Replace** the old chat UI entirely: no `--plain` mode, no `--tui` flag. `sakthai chat` always launches the TUI.
- Preserve full feature parity: streaming + final markdown, thinking spinner, tool-call traces, slash commands (`/help /tools /skills /memory /goal /clear /exit`), tab-completion + history + auto-suggest, welcome banner, persona colors/avatars, best-matched chip, per-turn status bar.
- Add `textual`; remove `prompt_toolkit`. Drop `theme.PERSONA_PROMPT_COLORS` (only prompt_toolkit used it).
- Tests hermetic (no network/credentials), `-m "not integration"` clean; keep the 85% branch-coverage floor (`fail_under` in `pyproject.toml`).
- Lint/type clean: `ruff check sakthai tests`, `ruff format --check`, `mypy sakthai` (strict). New module must be strict-clean.
- Reuse the existing history file path `config.sakthai_home()/"chat_history"`.

---

### Task 1: Add `textual`, drop `prompt_toolkit`

**Files:**
- Modify: `pyproject.toml` (dependencies array)

**Interfaces:**
- Consumes: nothing.
- Produces: `import textual` available; `prompt_toolkit` gone from deps.

- [ ] **Step 1: Edit dependencies**

In `pyproject.toml`, in `[project].dependencies`, remove the `prompt_toolkit` line and add textual (keep alphroughly grouped near `rich`):

```toml
    "rich>=13.7,<15.0",
    "textual>=0.79,<2.0",
```

Delete the line:

```toml
    "prompt_toolkit>=3.0,<4.0",
```

- [ ] **Step 2: Sync the environment**

Run: `uv sync --all-extras`
Expected: resolves and installs `textual`; no `prompt_toolkit`.

- [ ] **Step 3: Verify import**

Run: `uv run python -c "import textual; print(textual.__version__)"`
Expected: prints a version (e.g. `0.86.x`), exit 0.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add textual, drop prompt_toolkit for chat TUI"
```

---

### Task 2: Extract pure renderable builders + side-effect-free slash handler in `chat.py`

Pull the renderable construction out of the print-driven functions so the TUI and unit tests share one source of truth. Leave the old `run_chat` loop in place for now (removed in Task 7).

**Files:**
- Modify: `sakthai/agent/chat.py`
- Test: `tests/test_chat_builders.py` (create)

**Interfaces:**
- Consumes: `ui.py` builders, `theme.py` constants (Task-independent, already exist).
- Produces (new public functions in `sakthai/agent/chat.py`):
  - `user_panel(text: str) -> Panel`
  - `tool_trace(payload: dict[str, Any], *, persona: str | None = None) -> Text` — one renderable per tool_call event (glyph+name+args, error mark, and result preview folded in on a second line via `Text` with `\n`).
  - `reply_panel(parts: list[str], *, persona: str, matched: tuple[str, str] | None, streaming: bool) -> Panel` — `Text` body while `streaming=True`, `Markdown` body when `False`.
  - `error_text(exc: Exception) -> Text`
  - `cancelled_text() -> Text`
  - `slash_result(command: str, *, persona: str, goal: str | None, store: MemoryStore | None, tools: tuple[Tool, ...]) -> tuple[bool, str | None, list[RenderableType]]` — side-effect-free replacement for `handle_slash_command`; returns `(handled, new_goal, renderables_to_mount)`. `/clear` returns `handled=True, goal=None, []` (the app clears the pane); `/help /tools /skills /memory` return the matching `ui.*_panel`; `/goal` returns a confirmation `Text`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_chat_builders.py`:

```python
"""Unit tests for the pure renderable builders extracted from chat.py."""

from __future__ import annotations

import io

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from sakthai.agent import chat as chat_agent
from sakthai.memory.store import MemoryStore


def _render(renderable: object) -> str:
    console = Console(file=io.StringIO(), force_terminal=False, width=100)
    console.print(renderable)
    return console.file.getvalue()  # type: ignore[union-attr]


def test_user_panel_wraps_text_in_panel() -> None:
    panel = chat_agent.user_panel("hello there")
    assert isinstance(panel, Panel)
    assert "hello there" in _render(panel)


def test_tool_trace_shows_name_args_and_preview() -> None:
    line = chat_agent.tool_trace(
        {"name": "read_file", "input": {"path": "x"}, "output_preview": "abc"},
        persona="sakthai",
    )
    text = _render(line)
    assert "read_file" in text
    assert "abc" in text


def test_reply_panel_streaming_is_plain_text_body() -> None:
    panel = chat_agent.reply_panel(
        ["hi ", "there"], persona="sakthai", matched=None, streaming=True
    )
    assert isinstance(panel.renderable, Text)
    assert "hi there" in _render(panel)


def test_reply_panel_final_is_markdown_body() -> None:
    panel = chat_agent.reply_panel(
        ["# Title"], persona="sakthai", matched=None, streaming=False
    )
    assert isinstance(panel.renderable, Markdown)


def test_slash_help_returns_a_panel_and_handled() -> None:
    handled, goal, renderables = chat_agent.slash_result(
        "/help", persona="sakthai", goal=None, store=None, tools=()
    )
    assert handled is True
    assert len(renderables) == 1


def test_slash_goal_sets_goal_and_returns_confirmation() -> None:
    handled, goal, renderables = chat_agent.slash_result(
        "/goal ship the TUI", persona="sakthai", goal=None, store=None, tools=()
    )
    assert handled is True
    assert goal == "ship the TUI"
    assert "ship the TUI" in _render(renderables[0])


def test_slash_clear_signals_reset_with_no_renderables() -> None:
    handled, goal, renderables = chat_agent.slash_result(
        "/clear", persona="sakthai", goal="x", store=None, tools=()
    )
    assert handled is True
    assert goal is None
    assert renderables == []


def test_non_slash_input_is_not_handled() -> None:
    handled, goal, renderables = chat_agent.slash_result(
        "just a message", persona="sakthai", goal="keep", store=None, tools=()
    )
    assert handled is False
    assert goal == "keep"
    assert renderables == []


def test_slash_memory_uses_store_when_present() -> None:
    store = MemoryStore(":memory:")
    handled, _goal, renderables = chat_agent.slash_result(
        "/memory", persona="sakthai", goal=None, store=store, tools=()
    )
    assert handled is True
    assert len(renderables) == 1
    store.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat_builders.py -q`
Expected: FAIL — `AttributeError: module 'sakthai.agent.chat' has no attribute 'user_panel'` (etc.).

- [ ] **Step 3: Implement the builders**

In `sakthai/agent/chat.py`, add these functions (place near the existing renderers). Reuse existing imports (`box`, `Panel`, `Text`, `Markdown`, `RenderableType`, `time`, theme glyphs/colors, `chip`, `persona_avatar`, `help_panel`, `tools_panel`, `memory_panel`, `skills_panel`, and the collect_skills import used by `render_skills`):

```python
def user_panel(text: str) -> Panel:
    """The user's message as a blue titled panel (plain text, never markup)."""
    return Panel(
        Text(text),
        box=box.ROUNDED,
        title=f"[bold {USER_COLOR}]{USER_AVATAR} you[/bold {USER_COLOR}]",
        title_align="left",
        subtitle=f"[dim]{time.strftime('%H:%M')}[/dim]",
        subtitle_align="right",
        border_style=USER_COLOR,
    )


def tool_trace(payload: dict[str, Any], *, persona: str | None = None) -> Text:
    """One trace renderable for a tool_call event: name + args, plus preview line."""
    accent = PERSONA_ACCENTS.get(persona or "", "cyan")
    line = Text()
    line.append(f"{GLYPH_TOOL} {payload['name']}", style=f"bold {accent}")
    line.append(_truncate(f"({payload['input']})"), style="dim")
    if payload.get("is_error"):
        line.append(f" {GLYPH_ERROR}", style="bold red")
    preview = payload.get("output_preview")
    if preview:
        line.append(f"\n  {GLYPH_RESULT} ", style=accent)
        line.append(str(preview), style="dim italic")
    return line


def _reply_title(persona: str, matched: tuple[str, str] | None) -> tuple[str, str, str]:
    display = matched[0] if matched else persona
    label = PERSONA_LABELS.get(display, display)
    color = PERSONA_COLORS.get(display, "white")
    return label, color, persona_avatar(display)


def reply_panel(
    parts: list[str],
    *,
    persona: str,
    matched: tuple[str, str] | None,
    streaming: bool,
) -> Panel:
    """The persona reply panel: plain Text while streaming, Markdown when final."""
    label, color, avatar = _reply_title(persona, matched)
    body: RenderableType
    body = Text("".join(parts)) if streaming else Markdown("".join(parts))
    if streaming:
        subtitle: RenderableType = "[dim]▌ streaming…[/dim]"
    elif matched:
        subtitle = chip(f"best matched: {label} · {matched[1]}", accent=color, glyph=avatar)
    else:
        subtitle = f"[dim]{time.strftime('%H:%M')}[/dim]"
    return Panel(
        body,
        box=box.ROUNDED,
        title=f"[{color}]{avatar}[/{color}] [bold {color}]{label}[/bold {color}]",
        title_align="left",
        subtitle=subtitle,
        subtitle_align="right",
        border_style=color,
    )


def error_text(exc: Exception) -> Text:
    return Text.from_markup(f"[bold red]{GLYPH_ERROR} error:[/bold red] {exc}")


def cancelled_text() -> Text:
    return Text.from_markup(f"[yellow]{GLYPH_CANCEL} cancelled[/yellow]")


def slash_result(
    command: str,
    *,
    persona: str,
    goal: str | None,
    store: MemoryStore | None,
    tools: tuple[Tool, ...] = (),
) -> tuple[bool, str | None, list[RenderableType]]:
    """Side-effect-free slash-command handler; returns (handled, goal, renderables)."""
    stripped = command.strip()
    if not stripped.startswith("/"):
        return False, goal, []
    verb, _, rest = stripped.partition(" ")
    rest = rest.strip()
    if verb == "/help":
        return True, goal, [help_panel(persona=persona)]
    if verb == "/tools":
        return True, goal, [tools_panel(tools, persona=persona)]
    if verb == "/skills":
        from ..skills import collect_skills, default_skill_roots

        skills = sorted(collect_skills(*default_skill_roots()), key=lambda s: s.name)
        return True, goal, [skills_panel(skills, persona=persona)]
    if verb == "/memory":
        if store is None:
            return True, goal, []
        return True, goal, [memory_panel(store.list_facts(limit=15), persona=persona)]
    if verb == "/clear":
        return True, None, []
    if verb == "/goal":
        if not rest:
            msg = "goal cleared" if goal else "usage: /goal <what you want to accomplish>"
            return True, None, [Text.from_markup(f"[dim]{msg}[/dim]")]
        return True, rest, [Text.from_markup(f"[bold]🎯 goal set:[/bold] [italic]{rest}[/italic]")]
    return False, goal, []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat_builders.py -q`
Expected: PASS (9 passed).

- [ ] **Step 5: Lint/type the module**

Run: `uv run ruff check sakthai/agent/chat.py && uv run mypy sakthai/agent/chat.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/chat.py tests/test_chat_builders.py
git commit -m "refactor: extract pure renderable builders + slash_result in chat.py"
```

---

### Task 3: Textual app skeleton (`tui.py`) — layout only

Build the app shell: welcome banner, scrolling conversation pane, bottom input, footer. No agent yet.

**Files:**
- Create: `sakthai/agent/tui.py`
- Test: `tests/test_tui_app.py` (create)

**Interfaces:**
- Consumes: `chat_agent.*` builders (Task 2); `ui.welcome_panel`, `ui.status_bar`; `theme.*`; `config.sakthai_home`.
- Produces: `SakThaiApp` with constructor
  `SakThaiApp(*, persona, soul_text, tools, model, provider, caveman, with_skills, store)` and instance attributes `persona`, `model`, `provider`, `store`, `tools`, `goal`, `prior_messages`. Widget ids: `#conversation` (VerticalScroll), `#compose` (Input), `#status` (Static footer). Method `mount_renderable(renderable) -> None` that mounts a `Static` into `#conversation` and scrolls to end. Method `refresh_status(elapsed: float | None = None) -> None`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tui_app.py`:

```python
"""Pilot tests for the Textual chat app."""

from __future__ import annotations

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

from sakthai.agent.tui import SakThaiApp
from sakthai.memory.store import MemoryStore


def _app() -> SakThaiApp:
    return SakThaiApp(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="sakthai",
        provider="ollama",
        caveman=None,
        with_skills=(),
        store=MemoryStore(":memory:"),
    )


@pytest.mark.asyncio
async def test_app_mounts_core_widgets() -> None:
    app = _app()
    async with app.run_test() as pilot:
        assert pilot.app.query_one("#conversation", VerticalScroll) is not None
        assert pilot.app.query_one("#compose", Input) is not None
        assert pilot.app.query_one("#status", Static) is not None
    app.store.close()


@pytest.mark.asyncio
async def test_mount_renderable_adds_child_to_conversation() -> None:
    app = _app()
    async with app.run_test() as pilot:
        before = len(pilot.app.query_one("#conversation").children)
        pilot.app.mount_renderable("hello")
        await pilot.pause()
        after = len(pilot.app.query_one("#conversation").children)
        assert after == before + 1
    app.store.close()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tui_app.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'sakthai.agent.tui'`.

- [ ] **Step 3: Implement the app skeleton**

Create `sakthai/agent/tui.py`:

```python
"""Full-screen Textual chat app: conversation pane above a pinned input.

Backs ``sakthai chat``. Reuses the Rich renderables built in
``sakthai.agent.chat`` and ``sakthai.agent.ui`` by mounting them into Textual
``Static`` widgets, so the persona look is preserved. ``run_agent`` runs in a
worker thread; token/tool callbacks marshal to the UI via ``call_from_thread``.
"""

from __future__ import annotations

from typing import Any

from rich.console import RenderableType
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

from .. import __version__
from ..memory.store import MemoryStore
from . import chat as chat_agent
from .theme import GLYPH_PROMPT, PERSONA_COLORS
from .tools import Tool
from .ui import status_bar, welcome_panel


class SakThaiApp(App[None]):
    """The interactive chat application."""

    CSS = """
    #conversation { height: 1fr; padding: 0 1; }
    #compose { dock: bottom; border: round $accent; }
    #status { dock: bottom; height: 1; padding: 0 1; }
    """

    BINDINGS = [("ctrl+c", "cancel_turn", "cancel")]

    def __init__(
        self,
        *,
        persona: str,
        soul_text: str,
        tools: tuple[Tool, ...],
        model: str,
        provider: str | None,
        caveman: str | None,
        with_skills: tuple[str, ...],
        store: MemoryStore,
    ) -> None:
        super().__init__()
        self.persona = persona
        self.soul_text = soul_text
        self.tools = tools
        self.model = model
        self.provider = provider
        self.caveman = caveman
        self.with_skills = with_skills
        self.store = store
        self.goal: str | None = None
        self.prior_messages: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Static(
            welcome_panel(
                persona=self.persona,
                model=self.model,
                provider=self.provider,
                tool_count=len(self.tools),
                facts=self.store.stats()["facts"]["total"],
                version=__version__,
                goal=self.goal,
            ),
            id="banner",
        )
        yield VerticalScroll(id="conversation")
        yield Static(self._status_renderable(), id="status")
        color = PERSONA_COLORS.get(self.persona, "white")
        compose = Input(placeholder=f"{GLYPH_PROMPT} message  ·  /help", id="compose")
        compose.styles.border = ("round", color)
        yield compose

    def on_mount(self) -> None:
        self.query_one("#compose", Input).focus()

    def _status_renderable(self, elapsed: float | None = None) -> RenderableType:
        return status_bar(
            persona=self.persona,
            model=self.model,
            tool_count=len(self.tools),
            facts=self.store.stats()["facts"]["total"],
            elapsed=elapsed,
            goal=self.goal,
        )

    def refresh_status(self, elapsed: float | None = None) -> None:
        self.query_one("#status", Static).update(self._status_renderable(elapsed))

    def mount_renderable(self, renderable: RenderableType) -> Static:
        widget = Static(renderable)
        pane = self.query_one("#conversation", VerticalScroll)
        pane.mount(widget)
        pane.scroll_end(animate=False)
        return widget

    def action_cancel_turn(self) -> None:  # extended in Task 5
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_tui_app.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Lint/type**

Run: `uv run ruff check sakthai/agent/tui.py && uv run mypy sakthai/agent/tui.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/tui.py tests/test_tui_app.py
git commit -m "feat: Textual chat app skeleton (layout, banner, input, status)"
```

---

### Task 4: Slash commands + submit routing in the app

Wire the `Input.Submitted` event to `slash_result`, mount returned renderables, apply `/clear` and `/exit`, and mount the user panel for non-command input (agent run comes in Task 5).

**Files:**
- Modify: `sakthai/agent/tui.py`
- Test: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `chat_agent.slash_result`, `chat_agent.user_panel`.
- Produces: `on_input_submitted(self, event: Input.Submitted) -> None`; a `_submit(text: str) -> None` helper returning early when a slash command was handled; `#conversation` cleared on `/clear`; `self.exit()` on `/exit`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_tui_app.py`:

```python
async def _type_and_enter(pilot: object, text: str) -> None:
    app = pilot.app  # type: ignore[attr-defined]
    app.query_one("#compose", Input).value = text
    await pilot.press("enter")  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_help_command_mounts_a_panel_and_clears_input() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/help")
        assert len(pilot.app.query_one("#conversation").children) == 1
        assert pilot.app.query_one("#compose", Input).value == ""
    app.store.close()


@pytest.mark.asyncio
async def test_goal_command_sets_goal() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/goal ship it")
        assert pilot.app.goal == "ship it"
    app.store.close()


@pytest.mark.asyncio
async def test_clear_command_empties_conversation() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/help")
        await _type_and_enter(pilot, "/clear")
        assert len(pilot.app.query_one("#conversation").children) == 0
    app.store.close()


@pytest.mark.asyncio
async def test_exit_command_stops_the_app() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/exit")
        await pilot.pause()
        assert not pilot.app.is_running
    app.store.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tui_app.py -q`
Expected: FAIL — submitting does nothing (input keeps its value / no children mounted).

- [ ] **Step 3: Implement submit routing**

In `sakthai/agent/tui.py`, add the import `from .chat import slash_result, user_panel` (or use `chat_agent.` prefix) and these methods on `SakThaiApp`:

```python
    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self.query_one("#compose", Input).value = ""
        if not text:
            return
        self._submit(text)

    def _submit(self, text: str) -> None:
        if text == "/exit":
            self.exit()
            return
        if text.startswith("/"):
            handled, self.goal, renderables = chat_agent.slash_result(
                text,
                persona=self.persona,
                goal=self.goal,
                store=self.store,
                tools=self.tools,
            )
            if handled:
                if text.split()[0] == "/clear":
                    self.query_one("#conversation", VerticalScroll).remove_children()
                for renderable in renderables:
                    self.mount_renderable(renderable)
                self.refresh_status()
                return
        self.mount_renderable(chat_agent.user_panel(text))
        self._run_turn(text)  # implemented in Task 5

    def _run_turn(self, text: str) -> None:  # replaced in Task 5
        pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tui_app.py -q`
Expected: PASS.

- [ ] **Step 5: Lint/type**

Run: `uv run ruff check sakthai/agent/tui.py && uv run mypy sakthai/agent/tui.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/tui.py tests/test_tui_app.py
git commit -m "feat: slash-command routing + submit handling in chat TUI"
```

---

### Task 5: Turn lifecycle — worker thread, streaming, tool traces, status

Run `run_agent` in a worker thread; show a thinking spinner, stream tokens into a reply panel, mount tool traces, finalize to markdown, update status, and handle errors/cancel.

**Files:**
- Modify: `sakthai/agent/tui.py`
- Test: `tests/test_tui_app.py`

**Interfaces:**
- Consumes: `run_agent`, `AgentError`, `AgentResult` from `..agent.loop`; `match_persona` from `.persona_match`; `chat_agent.reply_panel/tool_trace/error_text/cancelled_text`; `_goal_prompt_prefix` from `.chat`.
- Produces: a `ReplyView(Static)` widget with `start_thinking()`, `append(delta: str)`, `finalize()`, `set_error(exc)`, `set_cancelled()`; `SakThaiApp._run_turn(text)` launching a threaded worker; `action_cancel_turn` cancels the active worker.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_tui_app.py` (mock `run_agent` at the `tui` module boundary):

```python
from sakthai.agent.loop import AgentResult
import sakthai.agent.tui as tui_mod


def _fake_run_agent_factory(reply: str, tool: bool = False):
    def _fake(task, **kwargs):  # noqa: ANN001, ANN003
        on_event = kwargs.get("on_event")
        on_token = kwargs.get("on_token")
        if tool and on_event:
            on_event("tool_call", {"name": "read_file", "input": {"p": 1}, "output_preview": "ok"})
        if on_token:
            for ch in reply:
                on_token(ch)
        return AgentResult(text=reply, iterations=1, stop_reason="end", messages=[{"role": "x"}])
    return _fake


@pytest.mark.asyncio
async def test_turn_streams_reply_and_records_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_factory("hello"))
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause(0.2)
        # user panel + reply widget both present
        assert len(pilot.app.query_one("#conversation").children) >= 2
        assert pilot.app.prior_messages == [{"role": "x"}]
    app.store.close()


@pytest.mark.asyncio
async def test_turn_mounts_tool_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_factory("done", tool=True))
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "use a tool"
        await pilot.press("enter")
        await pilot.pause(0.2)
        texts = [str(c.renderable) for c in pilot.app.query_one("#conversation").children]  # type: ignore[attr-defined]
        assert any("read_file" in t for t in texts)
    app.store.close()


@pytest.mark.asyncio
async def test_turn_error_is_shown(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(task, **kwargs):  # noqa: ANN001, ANN003
        from sakthai.agent.loop import AgentError

        raise AgentError("nope")

    monkeypatch.setattr(tui_mod, "run_agent", _boom)
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause(0.2)
        texts = [str(c.renderable) for c in pilot.app.query_one("#conversation").children]  # type: ignore[attr-defined]
        assert any("nope" in t for t in texts)
    app.store.close()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tui_app.py -k "turn" -q`
Expected: FAIL — `_run_turn` is a no-op, so no reply/history/trace.

- [ ] **Step 3: Implement the reply widget and turn worker**

In `sakthai/agent/tui.py` add imports:

```python
import time

from rich.spinner import Spinner
from rich.text import Text
from textual.worker import Worker, WorkerState

from .loop import AgentError, run_agent
from .persona_match import match_persona
```

Add the `ReplyView` widget (module level):

```python
class ReplyView(Static):
    """A single reply: animated spinner -> streamed text -> final markdown."""

    def __init__(self, persona: str, matched: tuple[str, str] | None) -> None:
        super().__init__()
        self._persona = persona
        self._matched = matched
        self._parts: list[str] = []
        self._timer: Any = None

    def start_thinking(self) -> None:
        from .theme import PERSONA_COLORS

        color = PERSONA_COLORS.get(self._persona, "white")
        spinner = Spinner("dots", text=Text(" thinking…", style=color), style=color)
        self._timer = self.set_interval(1 / 12, lambda: self.update(spinner))

    def _stop_timer(self) -> None:
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def append(self, delta: str) -> None:
        self._stop_timer()
        self._parts.append(delta)
        self.update(
            chat_agent.reply_panel(
                self._parts, persona=self._persona, matched=self._matched, streaming=True
            )
        )

    def finalize(self) -> None:
        self._stop_timer()
        self.update(
            chat_agent.reply_panel(
                self._parts, persona=self._persona, matched=self._matched, streaming=False
            )
        )

    def set_error(self, exc: Exception) -> None:
        self._stop_timer()
        self.update(chat_agent.error_text(exc))

    def set_cancelled(self) -> None:
        self._stop_timer()
        self.update(chat_agent.cancelled_text())
```

Replace the stub `_run_turn`/`action_cancel_turn` on `SakThaiApp` with:

```python
    def _run_turn(self, text: str) -> None:
        matched = match_persona(text)
        reply = ReplyView(self.persona, matched)
        pane = self.query_one("#conversation", VerticalScroll)
        pane.mount(reply)
        pane.scroll_end(animate=False)
        reply.start_thinking()
        self._turn_started = time.perf_counter()
        self._active_reply = reply
        self.run_worker(
            lambda: self._agent_call(text, reply),
            thread=True,
            exclusive=True,
            group="turn",
        )

    def _agent_call(self, text: str, reply: ReplyView) -> None:
        def on_token(delta: str) -> None:
            self.call_from_thread(reply.append, delta)

        def on_event(kind: str, payload: dict[str, Any]) -> None:
            if kind == "tool_call":
                self.call_from_thread(
                    self.mount_renderable, chat_agent.tool_trace(payload, persona=self.persona)
                )

        try:
            result = run_agent(
                text,
                history=self.prior_messages,
                system_prompt_prefix=chat_agent._goal_prompt_prefix(self.soul_text, self.goal),
                model=self.model,
                provider=self.provider,
                tools=self.tools,
                caveman=self.caveman,
                skills=list(self.with_skills),
                store=self.store,
                on_event=on_event,
                on_token=on_token,
            )
        except AgentError as exc:
            self.call_from_thread(reply.set_error, exc)
            return
        self.prior_messages = result.messages
        self.call_from_thread(reply.finalize)
        self.call_from_thread(self.refresh_status, time.perf_counter() - self._turn_started)

    def action_cancel_turn(self) -> None:
        self.workers.cancel_group(self, "turn")
        reply = getattr(self, "_active_reply", None)
        if reply is not None:
            reply.set_cancelled()
```

Initialize `self._active_reply: ReplyView | None = None` and `self._turn_started = 0.0` in `__init__`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tui_app.py -q`
Expected: PASS (all app tests).

- [ ] **Step 5: Lint/type**

Run: `uv run ruff check sakthai/agent/tui.py && uv run mypy sakthai/agent/tui.py`
Expected: no errors. (If mypy flags `_goal_prompt_prefix` as private cross-module use, promote it to `goal_prompt_prefix` in `chat.py` and update the call.)

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/tui.py tests/test_tui_app.py
git commit -m "feat: streaming turn lifecycle, tool traces, cancel in chat TUI"
```

---

### Task 6: Input history + auto-suggest + slash completion

Add a `Suggester` that suggests slash commands (when the line starts with `/`) and otherwise the most recent matching history entry; persist submitted lines to the history file.

**Files:**
- Modify: `sakthai/agent/tui.py`
- Test: `tests/test_tui_suggester.py` (create)

**Interfaces:**
- Consumes: `ui.SLASH_COMMANDS`, `config.sakthai_home`.
- Produces: `ChatSuggester(Suggester)` with `async def get_suggestion(self, value: str) -> str | None`; constructor `ChatSuggester(history: list[str])`; the app loads history from `chat_history` on mount, wires it as `Input(suggester=...)`, and appends each submitted line to the file.

- [ ] **Step 1: Write the failing test**

Create `tests/test_tui_suggester.py`:

```python
"""Tests for the chat input suggester (slash + history)."""

from __future__ import annotations

import pytest

from sakthai.agent.tui import ChatSuggester


@pytest.mark.asyncio
async def test_suggests_slash_command_by_prefix() -> None:
    s = ChatSuggester([])
    assert await s.get_suggestion("/he") == "/help"


@pytest.mark.asyncio
async def test_suggests_recent_history_by_prefix() -> None:
    s = ChatSuggester(["remember the milk", "read the file"])
    assert await s.get_suggestion("rem") == "remember the milk"


@pytest.mark.asyncio
async def test_no_suggestion_when_nothing_matches() -> None:
    s = ChatSuggester([])
    assert await s.get_suggestion("zzz") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tui_suggester.py -q`
Expected: FAIL — `ImportError: cannot import name 'ChatSuggester'`.

- [ ] **Step 3: Implement the suggester and wire it**

In `sakthai/agent/tui.py` add:

```python
from textual.suggester import Suggester

from .. import config
from .ui import SLASH_COMMANDS


class ChatSuggester(Suggester):
    """Suggest slash commands for '/'-prefixed input, else recent history."""

    def __init__(self, history: list[str]) -> None:
        super().__init__(use_cache=False, case_sensitive=True)
        self._history = history

    async def get_suggestion(self, value: str) -> str | None:
        if not value:
            return None
        if value.startswith("/"):
            for cmd, _args, _desc in SLASH_COMMANDS:
                if cmd.startswith(value) and cmd != value:
                    return cmd
            return None
        for entry in reversed(self._history):
            if entry.startswith(value) and entry != value:
                return entry
        return None
```

Add a history helper and wire it. In `__init__`, load history:

```python
        self._history_path = config.sakthai_home() / "chat_history"
        self._history: list[str] = self._load_history()
```

with:

```python
    def _load_history(self) -> list[str]:
        try:
            return self._history_path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []

    def _append_history(self, line: str) -> None:
        self._history.append(line)
        try:
            self._history_path.parent.mkdir(parents=True, exist_ok=True)
            with self._history_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass
```

In `compose`, build the input with the suggester:

```python
        compose = Input(
            placeholder=f"{GLYPH_PROMPT} message  ·  /help",
            id="compose",
            suggester=ChatSuggester(self._history),
        )
```

In `on_input_submitted`, before dispatching, persist non-empty lines:

```python
        if text:
            self._append_history(text)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tui_suggester.py tests/test_tui_app.py -q`
Expected: PASS.

- [ ] **Step 5: Lint/type**

Run: `uv run ruff check sakthai/agent/tui.py && uv run mypy sakthai/agent/tui.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/tui.py tests/test_tui_suggester.py
git commit -m "feat: slash + history suggester for chat TUI input"
```

---

### Task 7: Wire `cli/chat.py` to the app; remove old REPL + prompt_toolkit; update tests

Launch the app from the Click command, error clearly on non-TTY, and delete the superseded `run_chat` loop, prompt_toolkit helpers, and `PERSONA_PROMPT_COLORS`. Reconcile the old tests.

**Files:**
- Modify: `sakthai/cli/chat.py`
- Modify: `sakthai/agent/chat.py` (remove `run_chat`, `render_input_frame_*`, `ReplyStream`/`make_token_renderer`, `render_user_turn`, `render_error`, `render_cancelled`, `render_help/tools/memory/skills`, `handle_slash_command`, `status_line`, `animate_intro` if unused — keep `load_persona_soul`, `_goal_prompt_prefix`→`goal_prompt_prefix`, `render_banner` if reused; keep the new builders)
- Modify: `sakthai/agent/theme.py` (remove `PERSONA_PROMPT_COLORS` + its doc mention)
- Modify: `tests/test_chat.py`, `tests/test_cli_chat_helpers.py` (drop tests for removed symbols; keep `load_persona_soul` tests)
- Test: `tests/test_cli_chat_launch.py` (create)

**Interfaces:**
- Consumes: `SakThaiApp` (Task 3-6).
- Produces: `chat` Click command launches `SakThaiApp(...).run()`; on non-TTY, prints a message and exits non-zero.

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli_chat_launch.py`:

```python
"""The chat command wires options into SakThaiApp and runs it."""

from __future__ import annotations

from typing import Any

import pytest
from click.testing import CliRunner

import sakthai.cli.chat as chat_cli
from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_chat_constructs_and_runs_the_app(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, sakthai_home: object
) -> None:
    captured: dict[str, Any] = {}

    class _FakeApp:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(chat_cli, "SakThaiApp", _FakeApp)
    result = runner.invoke(main, ["chat", "--persona", "sakthai", "--no-mcp"])
    assert result.exit_code == 0, result.output
    assert captured.get("ran") is True
    assert captured["persona"] == "sakthai"
    assert captured["model"] == chat_cli.DEFAULT_CHAT_MODEL
```

(`sakthai_home` is the existing autouse-style fixture used by other CLI tests — reuse the same conftest fixture name; if it is not global, add `from tests... import` per the current pattern in `test_chat.py`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_chat_launch.py -q`
Expected: FAIL — `chat_cli` has no `SakThaiApp` / still calls `run_chat`.

- [ ] **Step 3: Rewrite `cli/chat.py`**

Replace the body of `sakthai/cli/chat.py` so the command builds and runs the app. Remove `_prompt_style`, `_bottom_toolbar`, `_slash_completer`, `_make_read_input`, and the `prompt_toolkit`/`Style` imports. Keep the Click options and `_tool_context`. New core:

```python
from ..agent.tui import SakThaiApp
...
    soul_text = load_persona_soul(persona)
    store = MemoryStore()
    try:
        with _tool_context(no_mcp=no_mcp, verbose=False) as tools:
            app = SakThaiApp(
                persona=persona,
                soul_text=soul_text,
                tools=tools,
                model=model,
                provider=provider,
                caveman=caveman,
                with_skills=with_skills,
                store=store,
            )
            app.run()
    finally:
        store.close()
```

(Textual raises on a non-terminal; wrap `app.run()` to translate it into a friendly click error:)

```python
            try:
                app.run()
            except Exception as exc:  # non-TTY / no terminal
                raise click.ClickException(
                    f"chat needs an interactive terminal ({exc}). "
                    "For non-interactive use, try: sakthai run \"<task>\"."
                ) from exc
```

- [ ] **Step 4: Remove superseded code and update `chat.py` / `theme.py`**

Delete from `sakthai/agent/chat.py`: `run_chat`, `render_input_frame_top`, `render_input_frame_bottom`, `ReplyStream`, `make_token_renderer`, `render_user_turn`, `render_error`, `render_cancelled`, `render_help`, `render_tools`, `render_memory`, `render_skills`, `handle_slash_command`, `status_line`, and `make_tool_renderer` (superseded by `tool_trace`); and `animate_intro`/`render_banner` if no longer referenced. Rename `_goal_prompt_prefix` to `goal_prompt_prefix` and update the reference in `tui.py`. Remove now-unused imports (`Live`, `input_frame_*`, `status_bar` if unused here, etc.). Delete `PERSONA_PROMPT_COLORS` and its docstring mention from `theme.py`.

Then update tests: in `tests/test_chat.py` delete tests that reference removed symbols (`render_user_turn`, `ReplyStream`, `handle_slash_command`, `run_chat`, `status_line`, `render_*`, and the `PERSONA_PROMPT_COLORS` assertion in `test_persona_labels_and_colors_cover_all_six_personas`); keep the `load_persona_soul` tests and the persona label/color coverage assertions minus the prompt-colors line. In `tests/test_cli_chat_helpers.py` delete tests for `_prompt_style`/`_bottom_toolbar`/`_slash_completer`/`_make_read_input`.

- [ ] **Step 5: Run the full suite + gates**

Run: `uv run pytest -m "not integration" -q`
Expected: PASS, no references to removed symbols.

Run: `uv run ruff check sakthai tests && uv run ruff format --check sakthai tests && uv run mypy sakthai`
Expected: clean.

Run: `uv run pytest -m "not integration" --cov=sakthai --cov-branch -q`
Expected: total coverage ≥ 85% (`fail_under` passes).

- [ ] **Step 6: Manual smoke check (real terminal)**

Run: `uv run sakthai chat --no-mcp` (with Ollama `sakthai` model available, per README).
Expected: full-screen TUI; input pinned at bottom; typing a message scrolls the conversation up; `/help` shows the panel; `/exit` quits.

- [ ] **Step 7: Commit**

```bash
git add sakthai/cli/chat.py sakthai/agent/chat.py sakthai/agent/theme.py tests/
git commit -m "feat: launch Textual TUI from chat command; remove old REPL + prompt_toolkit"
```

---

## Self-Review

**Spec coverage:**
- Full-screen TUI, input pinned bottom, scroll up → Tasks 3, 5. ✓
- Replace entirely, no plain/flag → Task 7 (cli rewrite + removals). ✓
- Streaming + markdown + spinner → Task 5 (`ReplyView`). ✓
- Tool traces → Tasks 2 (`tool_trace`) + 5. ✓
- Slash commands + completion + history/auto-suggest → Tasks 4 + 6. ✓
- Persona look + status bar + best-matched chip → Tasks 3 (banner/status), 2/5 (`reply_panel` chip). ✓
- Worker thread + `call_from_thread` → Task 5. ✓
- Add textual / drop prompt_toolkit / drop PERSONA_PROMPT_COLORS → Tasks 1 + 7. ✓
- TTY-only error handling → Task 7 Step 3. ✓
- Testing via Pilot + builder units, 85% floor → Tasks 2–7. ✓

**Placeholder scan:** No TBD/TODO; every code step has concrete code. The two forward-referenced stubs (`_run_turn`, `action_cancel_turn` in Tasks 3/4) are explicitly replaced in Task 5 with full code — intentional, not placeholders.

**Type consistency:** `slash_result` signature identical in Task 2 definition and Task 4 call. `reply_panel(parts, *, persona, matched, streaming)` identical across Tasks 2, 5. `mount_renderable`, `refresh_status`, `ReplyView.append/finalize/set_error/set_cancelled`, `ChatSuggester(history)` names consistent across tasks. `goal_prompt_prefix` rename applied in both `chat.py` (Task 7) and its `tui.py` caller — NOTE: Task 5 initially calls `chat_agent._goal_prompt_prefix`; Task 7 Step 4 renames it and updates the `tui.py` call. Executor must apply that rename in Task 7.
