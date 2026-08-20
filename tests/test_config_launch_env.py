"""Tests for the ``SAKTHAI_*`` launch-environment readers in ``config.py``.

These five readers are the env-var equivalents of the ``run``/``chat`` CLI
flags, and they are how the deployed personas are configured: the systemd unit
templates under ``infra/vm-agents/env-templates/`` set ``SAKTHAI_MODEL``,
``SAKTHAI_FAST`` and ``SAKTHAI_WITH_SKILLS`` for every agent, and
``telegram/bot.py`` reads them on every message.

Not one of them had a test. The parsing is not trivial — ``sakthai_with_skills``
splits on commas *and* whitespace, the boolean readers accept a fixed
vocabulary, and the string readers collapse whitespace-only values to ``None``
so that an env var present-but-empty (which is what an unfilled
``FOO=`` line in an env file produces) behaves the same as unset. Those are
exactly the cases that only fail in production.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai import config

BOOL_READERS = [
    (config.sakthai_fast_mode, "SAKTHAI_FAST"),
    (config.sakthai_skip_mcp, "SAKTHAI_NO_MCP"),
]

STRING_READERS = [
    (config.sakthai_default_provider, "SAKTHAI_PROVIDER"),
    (config.sakthai_default_model, "SAKTHAI_MODEL"),
]


# ---------------------------------------------------------------------------
# Boolean flags — SAKTHAI_FAST / SAKTHAI_NO_MCP
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reader", "env_var"), BOOL_READERS, ids=lambda p: getattr(p, "__name__", p)
)
@pytest.mark.parametrize("value", ["1", "true", "TRUE", "True", "yes", "YES", "on", "ON", " on "])
def test_boolean_readers_accept_truthy_vocabulary(
    reader: object, env_var: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(env_var, value)
    assert reader() is True


@pytest.mark.parametrize(
    ("reader", "env_var"), BOOL_READERS, ids=lambda p: getattr(p, "__name__", p)
)
@pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "   ", "maybe", "2", "y"])
def test_boolean_readers_reject_everything_else(
    reader: object, env_var: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Note ``y`` and ``2`` are *not* truthy — the vocabulary is closed, so an
    env file written with ``SAKTHAI_FAST=y`` silently runs in slow mode."""
    monkeypatch.setenv(env_var, value)
    assert reader() is False


@pytest.mark.parametrize(
    ("reader", "env_var"), BOOL_READERS, ids=lambda p: getattr(p, "__name__", p)
)
def test_boolean_readers_default_to_false_when_unset(
    reader: object, env_var: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(env_var, raising=False)
    assert reader() is False


# ---------------------------------------------------------------------------
# String overrides — SAKTHAI_PROVIDER / SAKTHAI_MODEL
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("reader", "env_var"), STRING_READERS, ids=lambda p: getattr(p, "__name__", p)
)
def test_string_readers_return_the_value(
    reader: object, env_var: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(env_var, "gemini-3.1-flash-lite")
    assert reader() == "gemini-3.1-flash-lite"


@pytest.mark.parametrize(
    ("reader", "env_var"), STRING_READERS, ids=lambda p: getattr(p, "__name__", p)
)
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_string_readers_treat_blank_as_unset(
    reader: object, env_var: str, value: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unfilled ``SAKTHAI_MODEL=`` line in an env file must fall through to
    the configured default, not override it with an empty model name."""
    monkeypatch.setenv(env_var, value)
    assert reader() is None


@pytest.mark.parametrize(
    ("reader", "env_var"), STRING_READERS, ids=lambda p: getattr(p, "__name__", p)
)
def test_string_readers_return_none_when_unset(
    reader: object, env_var: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(env_var, raising=False)
    assert reader() is None


def test_string_readers_do_not_strip_interior_whitespace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the surrounding whitespace is trimmed; the value is otherwise
    passed through untouched."""
    monkeypatch.setenv("SAKTHAI_MODEL", "  ollama/qwen2.5-coder  ")
    assert config.sakthai_default_model() == "ollama/qwen2.5-coder"


# ---------------------------------------------------------------------------
# SAKTHAI_WITH_SKILLS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("   ", []),
        ("one", ["one"]),
        ("one,two", ["one", "two"]),
        ("one, two,  three", ["one", "two", "three"]),
        # Whitespace is a separator too, not just commas.
        ("one two", ["one", "two"]),
        ("one\ttwo\nthree", ["one", "two", "three"]),
        # Empty segments from trailing/doubled commas are dropped.
        ("one,,two,", ["one", "two"]),
        (",", []),
        (" , , ", []),
        # Skill names keep their hyphens and Sak- prefixes intact.
        (
            "SakThai-daily-report,Sak-auto-cycle-loop",
            ["SakThai-daily-report", "Sak-auto-cycle-loop"],
        ),
    ],
)
def test_with_skills_splitting(
    raw: str, expected: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_WITH_SKILLS", raw)
    assert config.sakthai_with_skills() == expected


def test_with_skills_is_empty_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_WITH_SKILLS", raising=False)
    assert config.sakthai_with_skills() == []


# ---------------------------------------------------------------------------
# SAKTHAI_SYSTEM_PROMPT / SAKTHAI_SYSTEM_PROMPT_FILE
# ---------------------------------------------------------------------------


def test_inline_system_prompt_wins_over_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("from the file", encoding="utf-8")
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT", "inline wins")
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT_FILE", str(prompt_file))

    assert config.sakthai_system_prompt_prefix() == "inline wins"


def test_blank_inline_system_prompt_falls_through_to_the_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("  from the file  \n", encoding="utf-8")
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT", "   ")
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT_FILE", str(prompt_file))

    assert config.sakthai_system_prompt_prefix() == "from the file"


def test_unreadable_system_prompt_file_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing file must not take the launch down — the prefix is optional."""
    monkeypatch.delenv("SAKTHAI_SYSTEM_PROMPT", raising=False)
    monkeypatch.setenv("SAKTHAI_SYSTEM_PROMPT_FILE", "/nonexistent/prompt.txt")

    assert config.sakthai_system_prompt_prefix() is None


def test_no_system_prompt_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_SYSTEM_PROMPT", raising=False)
    monkeypatch.delenv("SAKTHAI_SYSTEM_PROMPT_FILE", raising=False)

    assert config.sakthai_system_prompt_prefix() is None
