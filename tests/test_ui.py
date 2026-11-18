"""Tests for sakthai.agent.ui — the chat CLI's reusable Rich components."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from sakthai import config
from sakthai.agent import theme, ui


def _render(renderable: object, *, terminal: bool = False) -> str:
    console = Console(file=io.StringIO(), force_terminal=terminal, width=120)
    console.print(renderable)
    return console.file.getvalue()  # type: ignore[union-attr]


def test_gradient_covers_every_persona() -> None:
    assert set(theme.PERSONA_GRADIENTS) == set(config.PERSONA_NAMES)
    assert set(theme.PERSONA_ACCENTS) == set(config.PERSONA_NAMES)


def test_gradient_text_preserves_the_plain_text() -> None:
    text = ui.gradient_text("SAK FAMILY", "#00d7ff", "#875fff")
    assert text.plain == "SAK FAMILY"


def test_gradient_text_fades_from_start_to_end_color() -> None:
    text = ui.gradient_text("abc", "#000000", "#ffffff", style="bold")
    spans = [span.style for span in text.spans]
    assert spans[0] == "bold #000000"
    assert spans[-1] == "bold #ffffff"


def test_gradient_text_single_char_uses_the_start_color() -> None:
    text = ui.gradient_text("x", "#112233", "#ffffff")
    assert text.spans[0].style == "#112233"


def test_chip_contains_glyph_and_text() -> None:
    out = _render(ui.chip("10 tools", accent="cyan", glyph="⚙"))
    assert "⚙" in out
    assert "10 tools" in out


def test_chip_without_glyph_renders_text_only() -> None:
    chip = ui.chip("ollama", accent="cyan")
    assert chip.plain == " ollama "


def test_chip_row_separates_chips_with_a_gutter() -> None:
    row = ui.chip_row(ui.chip("a", accent="red"), ui.chip("b", accent="blue"))
    assert row.plain == " a    b "


def test_persona_title_names_the_persona_and_terminal() -> None:
    title = ui.persona_title("sakthai")
    assert "SakThai" in title.plain
    assert "SAK FAMILY TERMINAL" in title.plain


def test_persona_title_falls_back_for_unknown_persona() -> None:
    title = ui.persona_title("ghost")
    assert "ghost" in title.plain


@pytest.mark.parametrize("facts", [None, 3])
def test_banner_panel_shows_model_provider_tools_and_hints(facts: int | None) -> None:
    out = _render(
        ui.banner_panel(
            persona="sakthai",
            model="sakthai",
            provider="ollama",
            tool_count=10,
            facts=facts,
            version="2.0.0",
        )
    )
    assert "SAK FAMILY TERMINAL" in out
    assert "ollama" in out
    assert "10 tools" in out
    assert "/exit" in out
    assert "v2.0.0" in out
    assert ("3 facts" in out) == (facts is not None)


def test_banner_panel_defaults_provider() -> None:
    out = _render(ui.banner_panel(persona="saksee", model="m", provider=None, tool_count=0))
    assert "default" in out


def test_banner_panel_emits_no_ansi_when_not_a_terminal() -> None:
    out = _render(ui.banner_panel(persona="sakthai", model="m", provider="ollama", tool_count=1))
    assert "\x1b[" not in out


def test_status_bar_reports_model_tools_facts_and_elapsed() -> None:
    bar = ui.status_bar(persona="sakthai", model="m1", tool_count=7, facts=2, elapsed=1.234)
    assert "m1" in bar.plain
    assert "7 tools" in bar.plain
    assert "2 facts" in bar.plain
    assert "1.2s" in bar.plain


def test_status_bar_omits_elapsed_when_not_given() -> None:
    bar = ui.status_bar(persona="sakthai", model="m", tool_count=1, facts=0)
    assert "⏱" not in bar.plain


def test_status_bar_shows_goal_when_pinned() -> None:
    bar = ui.status_bar(persona="sakthai", model="m", tool_count=1, facts=0, goal="ship it")
    assert "ship it" in bar.plain
    assert ui.status_bar(persona="sakthai", model="m", tool_count=1, facts=0).plain.count("🎯") == 0


def test_rainbow_has_seven_stops() -> None:
    assert len(theme.RAINBOW_STOPS) == 7


def test_multi_gradient_text_preserves_text_and_hits_each_endpoint() -> None:
    text = ui.multi_gradient_text("abcd", ("#000000", "#ff0000", "#0000ff"))
    assert text.plain == "abcd"
    assert text.spans[0].style == "#000000"
    assert text.spans[-1].style == "#0000ff"


def test_multi_gradient_text_empty_is_empty() -> None:
    assert ui.multi_gradient_text("", theme.RAINBOW_STOPS).plain == ""


def test_multi_gradient_text_single_stop_is_solid() -> None:
    text = ui.multi_gradient_text("abc", ("#123456",))
    assert {span.style for span in text.spans} == {"#123456"}


def test_rainbow_text_spans_the_spectrum() -> None:
    text = ui.rainbow_text("SAK FAMILY")
    assert text.plain == "SAK FAMILY"
    assert text.spans[0].style == "#ff5f5f"


def test_rainbow_rule_is_width_wide() -> None:
    rule = ui.rainbow_rule(20)
    assert rule.plain == "─" * 20


def test_avatars_cover_every_persona() -> None:
    assert set(theme.PERSONA_AVATARS) == set(config.PERSONA_NAMES)


def test_persona_avatar_returns_glyph_and_falls_back() -> None:
    assert ui.persona_avatar("sakthai") == theme.PERSONA_AVATARS["sakthai"]
    assert ui.persona_avatar("ghost") == "✻"


def test_rainbow_sweep_line_preserves_text_and_shifts_with_phase() -> None:
    a = ui.rainbow_sweep_line("SAKTHAI", phase=0.0)
    b = ui.rainbow_sweep_line("SAKTHAI", phase=0.5)
    assert a.plain == "SAKTHAI" == b.plain
    # A phase shift moves the hue under the first character.
    assert a.spans[0].style != b.spans[0].style


def test_rainbow_sweep_line_empty_is_empty() -> None:
    assert ui.rainbow_sweep_line("").plain == ""


def test_welcome_wordmark_uses_persona_avatar() -> None:
    out = _render(ui.welcome_panel(persona="sakthai", model="m", provider="ollama", tool_count=1))
    assert theme.PERSONA_AVATARS["sakthai"] in out


def test_status_bar_leads_with_persona_avatar() -> None:
    bar = ui.status_bar(persona="saksee", model="m", tool_count=1, facts=0)
    assert bar.plain.startswith(theme.PERSONA_AVATARS["saksee"])


def test_welcome_panel_shows_wordmark_chips_tips_and_goal() -> None:
    out = _render(
        ui.welcome_panel(
            persona="sakthai",
            model="sakthai",
            provider="ollama",
            tool_count=10,
            facts=3,
            version="2.0.0",
            goal="ship the release",
        )
    )
    assert "SAK FAMILY TERMINAL" in out
    assert "SakThai" in out
    assert "ollama" in out
    assert "10 tools" in out
    assert "3 facts" in out
    assert "/help" in out and "/goal" in out and "/exit" in out
    assert "v2.0.0" in out
    assert "ship the release" in out


def test_welcome_panel_without_goal_omits_goal_line() -> None:
    out = _render(ui.welcome_panel(persona="saksee", model="m", provider=None, tool_count=0))
    assert "default" in out
    assert "goal:" not in out


def test_banner_panel_is_welcome_panel_alias() -> None:
    assert ui.banner_panel is ui.welcome_panel


def test_help_panel_lists_every_command() -> None:
    out = _render(ui.help_panel(persona="sakthai"))
    for cmd in ("/help", "/tools", "/skills", "/memory", "/goal", "/clear", "/exit", "Ctrl-C"):
        assert cmd in out


def test_slash_commands_include_the_core_set() -> None:
    names = {cmd for cmd, *_ in ui.SLASH_COMMANDS}
    assert {"/help", "/tools", "/skills", "/memory", "/goal", "/clear", "/exit"} <= names


class _T:
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description


def test_tools_panel_lists_names_and_count() -> None:
    out = _render(
        ui.tools_panel(
            [_T("recall", "List facts"), _T("forget", "Delete a fact")], persona="sakthai"
        )
    )
    assert "tools · 2" in out
    assert "recall" in out and "forget" in out


def test_tools_panel_empty_message() -> None:
    assert "no tools available" in _render(ui.tools_panel([], persona="sakthai"))


class _F:
    def __init__(self, kind: str, key: str | None, value: str) -> None:
        self.kind = kind
        self.key = key
        self.value = value


def test_memory_panel_shows_facts_and_count() -> None:
    out = _render(
        ui.memory_panel(
            [_F("note", None, "likes rainbows"), _F("pref", "editor", "vim")], persona="sakthai"
        )
    )
    assert "memory · 2 facts" in out
    assert "likes rainbows" in out
    assert "editor" in out


def test_memory_panel_empty_message() -> None:
    assert "memory is empty" in _render(ui.memory_panel([], persona="sakthai"))


def test_memory_panel_treats_style_like_kind_as_literal_text() -> None:
    # A kind such as "red"/"bold" would be a valid Rich style; the label must be
    # shown literally, not interpreted as markup (and must not raise on render).
    out = _render(ui.memory_panel([_F("red", None, "the value")], persona="sakthai"), terminal=True)
    assert "[red]" in out
    assert "the value" in out


def test_listing_panel_shows_bracketed_tool_names_literally() -> None:
    out = _render(ui.tools_panel([_T("[weird]", "a tool")], persona="sakthai"), terminal=True)
    assert "[weird]" in out


def test_tools_panel_dedupes_shadowed_names_keeping_last() -> None:
    # An MCP tool shadowing a built-in by name: only the effective (last) one shows.
    out = _render(
        ui.tools_panel(
            [_T("recall", "built-in recall"), _T("recall", "MCP recall")], persona="sakthai"
        )
    )
    assert "tools · 1" in out
    assert "MCP recall" in out
    assert "built-in recall" not in out


def test_skills_panel_coerces_non_string_description() -> None:
    # A YAML description that parsed as a non-str must not crash the panel.
    out = _render(ui.skills_panel([_T("s", 12345)], persona="sakthai"))  # type: ignore[arg-type]
    assert "12345" in out


def test_help_panel_shows_goal_argument() -> None:
    out = _render(ui.help_panel(persona="sakthai"))
    assert "/goal <text>" in out


def test_skills_panel_lists_names_and_count() -> None:
    out = _render(
        ui.skills_panel(
            [_T("Sak-dogfood", "Try it yourself"), _T("Sak-yuanbao", "Do the thing")],
            persona="sakthai",
        )
    )
    assert "skills · 2" in out
    assert "Sak-dogfood" in out


def test_listing_panel_crops_long_description_without_wrapping() -> None:
    long_desc = "x" * 400
    out = _render(ui.tools_panel([_T("t", long_desc)], persona="sakthai"), terminal=True)
    # No un-indented spillover line: the single row stays one logical row.
    assert long_desc not in out  # cropped with an ellipsis


def test_memory_panel_truncates_long_values() -> None:
    # Values longer than 72 characters should be truncated with an ellipsis.
    long_value = "x" * 80
    out = _render(ui.memory_panel([_F("note", None, long_value)], persona="sakthai"))
    assert "…" in out
    assert long_value not in out
    # Exactly 71 chars of content + ellipsis
    assert long_value[:71] in out


def test_skills_panel_truncates_long_descriptions() -> None:
    # Descriptions longer than 72 characters should be truncated with an ellipsis.
    long_desc = "x" * 80
    out = _render(ui.skills_panel([_T("skill", long_desc)], persona="sakthai"))
    assert "…" in out
    assert long_desc not in out
    # Exactly 71 chars of content + ellipsis
    assert long_desc[:71] in out
