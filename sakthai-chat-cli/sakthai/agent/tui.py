"""Full-screen Textual chat app: conversation pane above a pinned input.

Backs ``sakthai chat``. Reuses the Rich renderables built in
``sakthai.agent.chat`` and ``sakthai.agent.ui`` by mounting them into Textual
``Static`` widgets, so the persona look is preserved. ``run_agent`` runs in a
worker thread; token/tool callbacks marshal to the UI via ``call_from_thread``.
"""

from __future__ import annotations

import time
from typing import Any

from rich.console import RenderableType
from rich.spinner import Spinner
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.suggester import Suggester
from textual.widgets import Input, Static

from .. import __version__, config
from ..memory.store import MemoryStore
from . import chat as chat_agent
from .loop import AgentResult, run_agent
from .persona_match import match_persona
from .theme import GLYPH_PROMPT, PERSONA_COLORS
from .tools import Tool
from .ui import SLASH_COMMANDS, status_bar, welcome_panel


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


class ReplyView(Static):
    """A single reply: animated spinner -> streamed text -> final markdown."""

    def __init__(self, persona: str, matched: tuple[str, str] | None) -> None:
        super().__init__()
        self._persona = persona
        self._matched = matched
        self._parts: list[str] = []
        self._timer: Any = None

    def start_thinking(self) -> None:
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
        self._active_reply: ReplyView | None = None
        self._turn_started = 0.0
        self._history_path = config.sakthai_home() / "chat_history"
        self._history: list[str] = self._load_history()

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
        compose = Input(
            placeholder=f"{GLYPH_PROMPT} message  ·  /help",
            id="compose",
            suggester=ChatSuggester(self._history),
        )
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

    def action_cancel_turn(self) -> None:
        reply = self._active_reply
        if reply is None:
            return
        self.workers.cancel_group(self, "turn")
        reply.set_cancelled()
        self._active_reply = None
        self.query_one("#compose", Input).disabled = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self.query_one("#compose", Input).value = ""
        if not text:
            return
        self._append_history(text)
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
        self._run_turn(text)

    def _run_turn(self, text: str) -> None:
        matched = match_persona(text)
        reply = ReplyView(self.persona, matched)
        pane = self.query_one("#conversation", VerticalScroll)
        pane.mount(reply)
        pane.scroll_end(animate=False)
        reply.start_thinking()
        self._turn_started = time.perf_counter()
        self._active_reply = reply
        # Single-flight: block another submit until this turn finishes,
        # errors, or is cancelled. Reduces concurrent access to the store and
        # stops rapid double-submit from racing two turns.
        self.query_one("#compose", Input).disabled = True
        history = self.prior_messages
        self.run_worker(
            lambda: self._agent_call(text, reply, history),
            thread=True,
            exclusive=True,
            group="turn",
        )

    # -- UI-thread targets for call_from_thread, below. Each first checks that
    # ``reply`` is still the current turn's reply (identity, not equality)
    # before mutating any shared state. The check and the mutation both run
    # on the single UI thread, so there is no time-of-check/time-of-use gap:
    # a stale worker's callback simply no-ops instead of clobbering a newer
    # or cancelled turn.

    def _apply_token(self, reply: ReplyView, delta: str) -> None:
        if reply is not self._active_reply:
            return
        reply.append(delta)

    def _apply_tool_event(self, reply: ReplyView, payload: dict[str, Any]) -> None:
        if reply is not self._active_reply:
            return
        self.mount_renderable(chat_agent.tool_trace(payload, persona=self.persona))

    def _apply_turn_success(self, reply: ReplyView, result: AgentResult) -> None:
        if reply is not self._active_reply:
            return
        self.prior_messages = result.messages
        reply.finalize()
        self.refresh_status(time.perf_counter() - self._turn_started)
        self._active_reply = None
        self.query_one("#compose", Input).disabled = False

    def _apply_turn_error(self, reply: ReplyView, exc: Exception) -> None:
        if reply is not self._active_reply:
            return
        reply.set_error(exc)
        self._active_reply = None
        self.query_one("#compose", Input).disabled = False

    def _agent_call(self, text: str, reply: ReplyView, history: list[dict[str, Any]]) -> None:
        def on_token(delta: str) -> None:
            self.call_from_thread(self._apply_token, reply, delta)

        def on_event(kind: str, payload: dict[str, Any]) -> None:
            if kind == "tool_call":
                self.call_from_thread(self._apply_tool_event, reply, payload)

        try:
            result = run_agent(
                text,
                history=history,
                system_prompt_prefix=chat_agent.goal_prompt_prefix(self.soul_text, self.goal),
                model=self.model,
                provider=self.provider,
                tools=self.tools,
                caveman=self.caveman,
                skills=list(self.with_skills),
                store=self.store,
                on_event=on_event,
                on_token=on_token,
            )
        except Exception as exc:  # noqa: BLE001 - any failure must reach the
            # reply panel via the identity-guarded UI callback rather than
            # tear down the whole app through the worker's exit_on_error.
            # chat_agent.error_text() already formats any exception, not just
            # AgentError.
            self.call_from_thread(self._apply_turn_error, reply, exc)
            return
        self.call_from_thread(self._apply_turn_success, reply, result)
