"""Reusable Rich components for the chat CLI's visual layer.

Small, purely presentational builders — gradient/rainbow wordmarks, metadata
chips, the full-screen welcome panel, turn-separator rules, the framed input
row, and the per-turn status bar. Everything here returns a Rich renderable
and touches no I/O, so :mod:`sakthai.agent.chat` stays the only place that
prints. Rich strips all color when the console is not a terminal, so these
components remain safe for pipes and tests.
"""

from __future__ import annotations

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .theme import (
    GLYPH_GOAL,
    GLYPH_REPLY,
    GLYPH_TOOL,
    PERSONA_ACCENTS,
    PERSONA_AVATARS,
    PERSONA_COLORS,
    PERSONA_GRADIENTS,
    PERSONA_LABELS,
    RAINBOW_STOPS,
)

#: Background tones for chips: a darker field for the glyph, a lighter one for text.
CHIP_BG = "grey19"

#: Dim tone for structural frame lines (input box, rules) — present but quiet.
FRAME_DIM = "grey42"

#: Fallbacks when an unknown persona name reaches the UI layer.
_FALLBACK_COLOR = "white"
_FALLBACK_GRADIENT = ("#d0d0d0", "#808080")

#: The in-REPL slash commands, defined once so the help panel, the welcome
#: tips line, and the prompt's tab-completer never drift apart. Each entry is
#: ``(command, args, description)`` — the completer inserts ``command`` alone,
#: while the help panel shows ``command args`` so required arguments are visible.
SLASH_COMMANDS: tuple[tuple[str, str, str], ...] = (
    ("/help", "", "show the command list"),
    ("/tools", "", "list the tools the agent can call"),
    ("/skills", "", "list available skills"),
    ("/memory", "", "show recent facts in memory"),
    ("/goal", "<text>", "pin a goal that steers replies; /goal alone clears it"),
    ("/clear", "", "clear the screen and history"),
    ("/exit", "", "end the session"),
)


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = value.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def multi_gradient_text(text: str, stops: tuple[str, ...], *, style: str = "") -> Text:
    """Color ``text`` character by character across an arbitrary run of hex ``stops``.

    Each character maps to a position in ``[0, 1]`` and is linearly interpolated
    between the two nearest stops, so a two-entry ``stops`` reproduces a simple
    fade and a seven-entry one paints a rainbow.
    """
    out = Text()
    if not text:
        return out
    if len(stops) == 1:
        stops = (stops[0], stops[0])
    rgb_stops = [_hex_to_rgb(s) for s in stops]
    segments = len(rgb_stops) - 1
    span = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        pos = (i / span) * segments
        left = min(int(pos), segments - 1)
        frac = pos - left
        (r1, g1, b1), (r2, g2, b2) = rgb_stops[left], rgb_stops[left + 1]
        r = round(r1 + (r2 - r1) * frac)
        g = round(g1 + (g2 - g1) * frac)
        b = round(b1 + (b2 - b1) * frac)
        out.append(ch, style=f"{style} #{r:02x}{g:02x}{b:02x}".strip())
    return out


def gradient_text(text: str, start: str, end: str, *, style: str = "") -> Text:
    """Two-stop fade from ``start`` to ``end`` hex (thin wrapper over multi_gradient_text)."""
    return multi_gradient_text(text, (start, end), style=style)


def rainbow_text(text: str, *, style: str = "") -> Text:
    """Paint ``text`` across the full :data:`RAINBOW_STOPS` spectrum."""
    return multi_gradient_text(text, RAINBOW_STOPS, style=style)


def rainbow_rule(width: int) -> Text:
    """A full-width horizontal rule drawn in the rainbow spectrum."""
    return rainbow_text("─" * max(width, 1))


def rainbow_sweep_line(text: str, *, phase: float = 0.0, style: str = "") -> Text:
    """Paint ``text`` in a rainbow that *cycles* — ``phase`` shifts the hues along.

    Unlike :func:`rainbow_text`, the spectrum wraps (position is taken modulo 1),
    so advancing ``phase`` from 0→1 animates the colors sweeping across the text.
    Used by the startup transformation.
    """
    out = Text()
    if not text:
        return out
    rgb_stops = [_hex_to_rgb(s) for s in RAINBOW_STOPS]
    segments = len(rgb_stops)
    span = max(len(text) - 1, 1)
    for i, ch in enumerate(text):
        t = ((i / span) + phase) % 1.0
        pos = t * segments
        left = int(pos) % segments
        right = (left + 1) % segments
        frac = pos - int(pos)
        (r1, g1, b1), (r2, g2, b2) = rgb_stops[left], rgb_stops[right]
        r = round(r1 + (r2 - r1) * frac)
        g = round(g1 + (g2 - g1) * frac)
        b = round(b1 + (b2 - b1) * frac)
        out.append(ch, style=f"{style} #{r:02x}{g:02x}{b:02x}".strip())
    return out


def persona_avatar(persona: str) -> str:
    """The persona's avatar glyph (falls back to the neutral sparkle)."""
    return PERSONA_AVATARS.get(persona, "✻")


def chip(text: str, *, accent: str, glyph: str | None = None) -> Text:
    """A pill-shaped metadata token: an accented glyph cell plus a text cell."""
    out = Text()
    if glyph:
        out.append(f" {glyph} ", style=f"bold {accent} on {CHIP_BG}")
    out.append(f" {text} ", style=f"bold on {CHIP_BG}")
    return out


def chip_row(*chips: Text) -> Text:
    """Join chips with a two-space gutter so the row scans as separate tokens."""
    row = Text()
    for i, item in enumerate(chips):
        if i:
            row.append("  ")
        row.append_text(item)
    return row


def persona_title(persona: str, *, suffix: str = "SAK FAMILY TERMINAL") -> Text:
    """``● <Label> · <suffix>`` with the suffix drawn in the persona gradient."""
    label = PERSONA_LABELS.get(persona, persona)
    color = PERSONA_COLORS.get(persona, _FALLBACK_COLOR)
    start, end = PERSONA_GRADIENTS.get(persona, _FALLBACK_GRADIENT)
    title = Text()
    title.append(f"{GLYPH_REPLY} {label}", style=f"bold {color}")
    title.append(" · ", style="dim")
    title.append_text(gradient_text(suffix, start, end, style="bold"))
    return title


def _metadata_chips(
    persona: str, model: str, provider: str | None, tool_count: int, facts: int | None
) -> list[Text]:
    accent = PERSONA_ACCENTS.get(persona, _FALLBACK_COLOR)
    chips = [
        chip(model, accent=accent, glyph=GLYPH_REPLY),
        chip(provider or "default", accent=accent, glyph="⇅"),
        chip(f"{tool_count} tools", accent=accent, glyph=GLYPH_TOOL),
    ]
    if facts is not None:
        chips.append(chip(f"{facts} facts", accent=accent, glyph="◆"))
    return chips


def welcome_panel(
    *,
    persona: str,
    model: str,
    provider: str | None,
    tool_count: int,
    facts: int | None = None,
    version: str | None = None,
    goal: str | None = None,
) -> Panel:
    """The full-screen session header: a Claude-Code-style welcome card.

    A rainbow sparkle wordmark, the metadata chip row, an optional pinned goal,
    and a dim "tips" line naming the slash commands — framed in a double-edge
    box in the persona color.
    """
    color = PERSONA_COLORS.get(persona, _FALLBACK_COLOR)
    accent = PERSONA_ACCENTS.get(persona, _FALLBACK_COLOR)
    label = PERSONA_LABELS.get(persona, persona)

    wordmark = Text()
    wordmark.append(f"{persona_avatar(persona)}  ", style="bold")
    wordmark.append(f"{label} ", style=f"bold {color}")
    wordmark.append_text(rainbow_text("· SAK FAMILY TERMINAL", style="bold"))

    tips = Text()
    tips.append("Tips: ", style="dim")
    for i, (cmd, desc) in enumerate(
        (("/help", "commands"), ("/goal", "pin a goal"), ("/clear", "reset"), ("/exit", "quit")),
    ):
        if i:
            tips.append("  ", style="dim")
        tips.append(cmd, style=f"bold {accent}")
        tips.append(f" {desc}", style="dim")

    parts: list[RenderableType] = [
        wordmark,
        Text(),
        chip_row(*_metadata_chips(persona, model, provider, tool_count, facts)),
    ]
    if goal:
        goal_line = Text()
        goal_line.append(f"{GLYPH_GOAL} goal: ", style=f"bold {accent}")
        goal_line.append(goal, style="italic")
        parts.extend((Text(), goal_line))
    parts.extend((Text(), tips))

    subtitle = Text(f"v{version}", style="dim") if version else None
    return Panel(
        Group(*parts),
        box=box.DOUBLE_EDGE,
        border_style=color,
        subtitle=subtitle,
        subtitle_align="right",
        padding=(1, 3),
    )


#: Back-compat alias: ``banner_panel`` was the pre-welcome name. Kept so callers
#: and tests that import it keep working; it now renders the welcome card.
banner_panel = welcome_panel


def status_bar(
    *,
    persona: str,
    model: str,
    tool_count: int,
    facts: int,
    elapsed: float | None = None,
    goal: str | None = None,
) -> Text:
    """The per-turn footer: colored segments joined by dim separators."""
    color = PERSONA_COLORS.get(persona, _FALLBACK_COLOR)
    accent = PERSONA_ACCENTS.get(persona, _FALLBACK_COLOR)
    bar = Text()
    bar.append(f"{persona_avatar(persona)} {model}", style=color)
    bar.append(" · ", style="dim")
    bar.append(f"{GLYPH_TOOL} {tool_count} tools", style=accent)
    bar.append(" · ", style="dim")
    bar.append(f"◆ {facts} facts", style="green")
    if elapsed is not None:
        bar.append(" · ", style="dim")
        bar.append(f"⏱ {elapsed:.1f}s", style="dim")
    if goal:
        bar.append(" · ", style="dim")
        bar.append(f"{GLYPH_GOAL} {goal}", style="italic yellow")
    return bar


def _listing_panel(
    title: str, rows: list[tuple[str, str]], *, persona: str, empty: str = ""
) -> Panel:
    """A rounded panel of ``name → description`` rows under a rainbow title.

    Descriptions render in a no-wrap column that crops with an ellipsis, so a
    long description never spills onto a second, un-indented line.
    """
    accent = PERSONA_ACCENTS.get(persona, _FALLBACK_COLOR)
    color = PERSONA_COLORS.get(persona, _FALLBACK_COLOR)
    body: RenderableType
    if not rows:
        body = Text(empty or "(nothing to show)", style="dim italic")
    else:
        grid = Table.grid(padding=(0, 2))
        grid.add_column(style=f"bold {accent}", no_wrap=True)
        grid.add_column(style="dim", no_wrap=True, overflow="ellipsis")
        for name, desc in rows:
            # Pass Text cells (not str) so bracketed content like "[note]" is
            # shown literally instead of being parsed as Rich markup/styles.
            grid.add_row(Text(name), Text(desc))
        body = grid
    return Panel(
        body,
        box=box.ROUNDED,
        border_style=color,
        title=rainbow_text(title),
        title_align="left",
        padding=(0, 2),
    )


def help_panel(*, persona: str) -> Panel:
    """A panel listing the in-REPL slash commands and key bindings."""
    rows = [(f"{cmd} {args}".strip(), desc) for cmd, args, desc in SLASH_COMMANDS]
    rows.append(("Ctrl-C", "cancel the current reply"))
    rows.append(("Ctrl-D", "end the session"))
    return _listing_panel("commands", rows, persona=persona)


def tools_panel(tools: object, *, persona: str) -> Panel:
    """List the tools the agent can call — name plus first-sentence description.

    Tools are collapsed by name (last wins) to mirror ``ToolRegistry``: when an
    external MCP server shadows a built-in, only the tool the agent will
    actually call is shown, matching the session's real capability set.
    """
    by_name: dict[str, str] = {}
    for tool in tools:  # type: ignore[attr-defined]
        name = str(getattr(tool, "name", "?"))
        desc = str(getattr(tool, "description", "") or "").strip().split(". ")[0].split("\n")[0]
        if len(desc) > 76:
            desc = desc[:75] + "…"
        by_name[name] = desc
    rows = list(by_name.items())
    return _listing_panel(f"tools · {len(rows)}", rows, persona=persona, empty="no tools available")


def memory_panel(facts: object, *, persona: str) -> Panel:
    """Show recent memory facts as ``[kind] key: value`` rows."""
    rows: list[tuple[str, str]] = []
    for fact in facts:  # type: ignore[attr-defined]
        kind = str(getattr(fact, "kind", "note"))
        key = getattr(fact, "key", None)
        value = str(getattr(fact, "value", "") or "").replace("\n", " ")
        if len(value) > 72:
            value = value[:71] + "…"
        label = f"[{kind}] {key}" if key else f"[{kind}]"
        rows.append((label, value))
    return _listing_panel(
        f"memory · {len(rows)} facts",
        rows,
        persona=persona,
        empty="memory is empty — tell me something to remember",
    )


def skills_panel(skills: object, *, persona: str) -> Panel:
    """List available skills — name plus short description."""
    rows: list[tuple[str, str]] = []
    for skill in skills:  # type: ignore[attr-defined]
        desc = str(getattr(skill, "description", "") or "").strip().split("\n")[0]
        if len(desc) > 72:
            desc = desc[:71] + "…"
        rows.append((str(getattr(skill, "name", "?")), desc))
    return _listing_panel(
        f"skills · {len(rows)}", rows, persona=persona, empty="no skills discovered"
    )
