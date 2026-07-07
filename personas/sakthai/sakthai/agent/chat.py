"""Interactive multi-turn chat: persona identity, rendering, and the REPL loop.

Backs ``sakthai chat``. Keeps `rich`/`prompt_toolkit` I/O at this module's
edges (renderers take an injected ``Console``; the loop takes an injected
``read_input`` callable) so the conversation-flow logic is testable without a
real terminal.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from rich.console import Console

from .. import config
from ..memory.store import MemoryStore

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
