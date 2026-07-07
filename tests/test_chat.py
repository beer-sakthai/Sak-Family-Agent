"""Tests for sakthai.agent.chat — persona identity, rendering, and the chat loop."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pytest
from rich.console import Console

from sakthai import config
from sakthai.agent import chat as chat_agent
from sakthai.memory.store import MemoryStore


def test_load_persona_soul_reads_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    persona_dir = tmp_path / "saksee"
    persona_dir.mkdir()
    (persona_dir / "SOUL.md").write_text("  SakSee identity text.  \n", encoding="utf-8")
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)
    assert chat_agent.load_persona_soul("saksee") == "SakSee identity text."


def test_load_persona_soul_missing_file_returns_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(config, "PERSONAS_DIR", tmp_path)
    with caplog.at_level(logging.WARNING):
        result = chat_agent.load_persona_soul("ghost")
    assert result == ""
    assert "ghost" in caplog.text


def test_persona_labels_and_colors_cover_all_six_personas() -> None:
    assert set(chat_agent.PERSONA_LABELS) == set(config.PERSONA_NAMES)
    assert set(chat_agent.PERSONA_COLORS) == set(config.PERSONA_NAMES)


def _console() -> Console:
    return Console(file=io.StringIO(), force_terminal=False, width=100)


def test_render_user_turn_prints_the_text() -> None:
    console = _console()
    chat_agent.render_user_turn(console, "what's in memory?")
    assert "what's in memory?" in console.file.getvalue()  # type: ignore[union-attr]


def test_tool_renderer_prints_name_input_and_output_preview() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event(
        "tool_call",
        {
            "name": "recall",
            "input": {"query": "*"},
            "is_error": False,
            "output_preview": "3 facts found",
        },
    )
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "recall" in output
    assert "3 facts found" in output


def test_tool_renderer_ignores_non_tool_events() -> None:
    console = _console()
    on_event = chat_agent.make_tool_renderer(console)
    on_event("iteration", {"n": 1, "stop_reason": "tool_use"})
    assert console.file.getvalue() == ""  # type: ignore[union-attr]


def test_token_renderer_prints_persona_label_once_then_streams_tokens() -> None:
    console = _console()
    on_token = chat_agent.make_token_renderer(console, "sakking")
    on_token("Hello")
    on_token(" there")
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert output.count("SakKing") == 1
    assert "Hello there" in output


def test_render_error_prints_the_exception_message() -> None:
    console = _console()
    chat_agent.render_error(console, RuntimeError("no credentials"))
    assert "no credentials" in console.file.getvalue()  # type: ignore[union-attr]


def test_render_cancelled_prints_a_marker() -> None:
    console = _console()
    chat_agent.render_cancelled(console)
    assert "cancelled" in console.file.getvalue().lower()  # type: ignore[union-attr]


def test_tool_renderer_emits_no_ansi_codes_when_not_a_terminal() -> None:
    console = _console()
    assert console.is_terminal is False
    on_event = chat_agent.make_tool_renderer(console)
    on_event(
        "tool_call",
        {"name": "recall", "input": {}, "is_error": False, "output_preview": "ok"},
    )
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "\x1b[" not in output


def test_status_line_reports_model_tools_and_fact_count(store: MemoryStore) -> None:
    store.add_fact("v1", kind="note", key="k1")
    line = chat_agent.status_line(store, "claude-opus-4-8", 5)
    assert "claude-opus-4-8" in line
    assert "5 tools" in line
    assert "1 facts" in line
