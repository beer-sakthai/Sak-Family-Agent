"""Persona theme for the chat CLI: labels, colors, and glyphs.

One place ties the whole interface to the active persona — the banner
border, the reply header, and the input prompt all draw from these maps.
"""

from __future__ import annotations

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

# Two-stop gradients (hex) per persona: the banner wordmark fades between
# these. Truecolor terminals show the fade; 256-color terminals snap each
# character to the nearest palette entry, which still reads as a two-tone mark.
PERSONA_GRADIENTS: dict[str, tuple[str, str]] = {
    "sakking": ("#ff5fd7", "#af5fff"),
    "sakthai": ("#00d7ff", "#875fff"),
    "saksee": ("#5fff87", "#00d787"),
    "saksit": ("#ffd75f", "#ff875f"),
    "saktan": ("#5f87ff", "#00afff"),
    "sakjules": ("#ff5f5f", "#ffaf5f"),
}

# Secondary accent per persona: chips, tool traces, and the status bar use it
# so a session reads as two coordinated tones rather than one flat color.
PERSONA_ACCENTS: dict[str, str] = {
    "sakking": "magenta",
    "sakthai": "bright_cyan",
    "saksee": "bright_green",
    "saksit": "bright_yellow",
    "saktan": "bright_blue",
    "sakjules": "bright_red",
}

# A distinct avatar glyph per persona, giving each Sak Family member a visual
# identity in the welcome wordmark, reply panels, and status bar.
PERSONA_AVATARS: dict[str, str] = {
    "sakking": "👑",
    "sakthai": "🐘",
    "saksee": "🎨",
    "saksit": "🧭",
    "saktan": "🌙",
    "sakjules": "⚙️",
}

# The user's side of the conversation is always this color and avatar.
USER_COLOR = "bright_blue"
USER_AVATAR = "🧑"

# A seven-stop spectrum (red → orange → yellow → green → cyan → blue → violet)
# used for persona-agnostic flourishes: the welcome wordmark, the turn-separator
# rules, and the sparkle glyph. Truecolor terminals show a smooth fade; 256-color
# terminals snap each character to the nearest palette entry and still read as a
# rainbow. Kept independent of the per-persona maps on purpose — this is the
# "everything, everywhere" accent Beer asked for, not a persona identity.
RAINBOW_STOPS: tuple[str, ...] = (
    "#ff5f5f",  # red
    "#ff9f43",  # orange
    "#ffd75f",  # yellow
    "#5fd75f",  # green
    "#00d7d7",  # cyan
    "#5f87ff",  # blue
    "#af5fff",  # violet
)

GLYPH_PROMPT = "❯"
GLYPH_TOOL = "⚙"
GLYPH_RESULT = "└─"
GLYPH_ERROR = "✗"
GLYPH_CANCEL = "■"
GLYPH_REPLY = "●"
GLYPH_SPARKLE = "✻"
GLYPH_GOAL = "🎯"
