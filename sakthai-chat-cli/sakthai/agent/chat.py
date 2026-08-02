"""Chat support: persona identity and pure Rich-renderable builders.

Backs ``sakthai chat`` (the Textual app in :mod:`sakthai.agent.tui`). The
builders here take plain data and return Rich renderables with no I/O of
their own, so they're testable without a real terminal and reusable by any
frontend that wants to mount them into a widget.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from rich import box
from rich.console import RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .. import config
from ..memory.store import MemoryStore
from .theme import (
    GLYPH_CANCEL,
    GLYPH_ERROR,
    GLYPH_RESULT,
    GLYPH_TOOL,
    PERSONA_ACCENTS,
    PERSONA_COLORS,
    PERSONA_LABELS,
    USER_AVATAR,
    USER_COLOR,
)
from .tools import Tool
from .ui import chip, help_panel, memory_panel, persona_avatar, skills_panel, tools_panel

logger = logging.getLogger(__name__)


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
