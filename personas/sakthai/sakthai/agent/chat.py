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
        logger.warning("No SOUL.md found for persona %r at %s; using base identity.", persona, path)
        return ""
