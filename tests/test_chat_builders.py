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
    panel = chat_agent.reply_panel(["# Title"], persona="sakthai", matched=None, streaming=False)
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
