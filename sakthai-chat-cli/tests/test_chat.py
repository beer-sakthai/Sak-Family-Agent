"""Tests for sakthai.agent.chat — persona identity (SOUL loading + theme coverage)."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from sakthai import config
from sakthai.agent import chat as chat_agent


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


def test_goal_prompt_prefix_appends_goal_directive() -> None:
    assert chat_agent.goal_prompt_prefix("SOUL", None) == "SOUL"
    combined = chat_agent.goal_prompt_prefix("SOUL", "ship the release")
    assert "SOUL" in combined
    assert "ship the release" in combined


def test_error_text_includes_the_exception_message() -> None:
    text = chat_agent.error_text(RuntimeError("no credentials"))
    assert "no credentials" in text.plain


def test_cancelled_text_shows_a_marker() -> None:
    text = chat_agent.cancelled_text()
    assert "cancelled" in text.plain.lower()
