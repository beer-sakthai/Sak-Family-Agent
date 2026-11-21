"""Interactive multi-turn chat: persona identity, rendering, and the REPL loop.

Backs ``sakthai chat``. Two frontends share this module:

* the inline REPL (:func:`run_chat`) keeps `rich`/`prompt_toolkit` I/O at this
  module's edges (renderers take an injected ``Console``; the loop takes an
  injected ``read_input`` callable) so the conversation flow is testable
  without a real terminal;
* the full-screen Textual app (:mod:`sakthai.agent.tui`) mounts the pure Rich
  builders below (``user_panel``, ``reply_panel``, ``slash_result`` …), which
  take plain data and return renderables with no I/O of their own.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from rich import box
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .. import config
from ..memory.store import MemoryStore
from .loop import AgentError, run_agent
from .theme import (
    GLYPH_CANCEL,
    GLYPH_ERROR,
    GLYPH_RESULT,
    GLYPH_TOOL,
    PERSONA_ACCENTS,
    USER_AVATAR,
    USER_COLOR,
)
from .theme import PERSONA_COLORS as THEME_PERSONA_COLORS
from .tools import Tool
from .ui import chip, help_panel, memory_panel, persona_avatar, skills_panel, tools_panel

logger = logging.getLogger(__name__)

PERSONA_LABELS: dict[str, str] = {
    "sakking": "SakKing",
    "sakthai": "SakThai",
    "saksee": "SakSee",
    "saksit": "SakSit",
    "sakjules": "SakJules",
    "saktan": "SakTan",
}

PERSONA_COLORS: dict[str, str] = {
    "sakking": "bright_magenta",
    "sakthai": "cyan",
    "saksee": "green",
    "saksit": "yellow",
    "sakjules": "bright_red",
    "saktan": "bright_blue",
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
        logger.warning("No SOUL.md found for persona %r at %s; using base identity.", persona, path)
        return ""


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
                persona=persona,
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


# ---------------------------------------------------------------------------
# Pure Rich builders for the full-screen Textual frontend (sakthai.agent.tui).
# Ported from the standalone sakthai-chat-cli; no I/O, so they're unit-testable.
# ---------------------------------------------------------------------------


def _truncate(value: str, limit: int = 80) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


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
    color = THEME_PERSONA_COLORS.get(display, "white")
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
        subtitle=subtitle,  # type: ignore[arg-type]
        subtitle_align="right",
        border_style=color,
    )


def error_text(exc: Exception) -> Text:
    return Text.from_markup(f"[bold red]{GLYPH_ERROR} error:[/bold red] {exc}")


def cancelled_text() -> Text:
    return Text.from_markup(f"[yellow]{GLYPH_CANCEL} cancelled[/yellow]")


def goal_prompt_prefix(soul_text: str, goal: str | None) -> str:
    """Fold an active session goal into the system-prompt prefix for the agent."""
    if not goal:
        return soul_text
    directive = (
        f"The user has pinned this session goal — keep it in mind and steer toward it: {goal}"
    )
    return f"{soul_text}\n\n{directive}".strip()


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

        skills = sorted(collect_skills(*default_skill_roots(persona)), key=lambda s: s.name)
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
