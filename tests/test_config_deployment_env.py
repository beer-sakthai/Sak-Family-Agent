"""Tests for deployment environment variable readers in config.py.

Finding 2 of docs/test-coverage-audit-2026-08-31.md: nine deployment env vars
had zero test references. These are tested here.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai import config


class TestDefaultProvider:
    """sakthai_default_provider() — SAKTHAI_PROVIDER env var."""

    def test_unset_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_PROVIDER", raising=False)
        assert config.sakthai_default_provider() is None

    def test_empty_string_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_PROVIDER", "")
        assert config.sakthai_default_provider() is None

    def test_whitespace_only_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_PROVIDER", "   \t  ")
        assert config.sakthai_default_provider() is None

    def test_returns_stripped_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_PROVIDER", "  anthropic  ")
        assert config.sakthai_default_provider() == "anthropic"

    def test_valid_provider_names(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for provider in ("anthropic", "google", "openai", "ollama", "gateway", "huggingface"):
            monkeypatch.setenv("SAKTHAI_PROVIDER", provider)
            assert config.sakthai_default_provider() == provider


class TestDefaultModel:
    """sakthai_default_model() — SAKTHAI_MODEL env var."""

    def test_unset_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_MODEL", raising=False)
        assert config.sakthai_default_model() is None

    def test_empty_string_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_MODEL", "")
        assert config.sakthai_default_model() is None

    def test_whitespace_only_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_MODEL", "   \t  ")
        assert config.sakthai_default_model() is None

    def test_returns_stripped_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_MODEL", "  claude-opus-4-8  ")
        assert config.sakthai_default_model() == "claude-opus-4-8"

    def test_hf_model_id_format(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        assert config.sakthai_default_model() == "Qwen/Qwen2.5-7B-Instruct"


class TestFastMode:
    """sakthai_fast_mode() — SAKTHAI_FAST env var."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("", False),
            ("0", False),
            ("false", False),
            ("no", False),
            ("off", False),
            ("disabled", False),
            ("1", True),
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("yes", True),
            ("YES", True),
            ("on", True),
            ("ON", True),
        ],
    )
    def test_truthy_values(
        self, monkeypatch: pytest.MonkeyPatch, value: str, expected: bool
    ) -> None:
        if value:
            monkeypatch.setenv("SAKTHAI_FAST", value)
        else:
            monkeypatch.delenv("SAKTHAI_FAST", raising=False)
        assert config.sakthai_fast_mode() is expected

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_FAST", "  true  ")
        assert config.sakthai_fast_mode() is True

    def test_unset_defaults_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_FAST", raising=False)
        assert config.sakthai_fast_mode() is False


class TestSkipMcp:
    """sakthai_skip_mcp() — SAKTHAI_NO_MCP env var."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("", False),
            ("0", False),
            ("false", False),
            ("no", False),
            ("off", False),
            ("1", True),
            ("true", True),
            ("yes", True),
            ("on", True),
        ],
    )
    def test_truthy_values(
        self, monkeypatch: pytest.MonkeyPatch, value: str, expected: bool
    ) -> None:
        if value:
            monkeypatch.setenv("SAKTHAI_NO_MCP", value)
        else:
            monkeypatch.delenv("SAKTHAI_NO_MCP", raising=False)
        assert config.sakthai_skip_mcp() is expected

    def test_whitespace_stripped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_NO_MCP", "  true  ")
        assert config.sakthai_skip_mcp() is True

    def test_unset_defaults_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_NO_MCP", raising=False)
        assert config.sakthai_skip_mcp() is False


class TestEvalLogPath:
    """eval_log_path() — SAKTHAI_EVAL_LOG env var override."""

    def test_uses_override_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_EVAL_LOG", "/custom/path/eval.jsonl")
        result = config.eval_log_path()
        assert result == Path("/custom/path/eval.jsonl")

    def test_uses_default_when_unset(self, monkeypatch: pytest.MonkeyPatch, _isolate_home) -> None:
        monkeypatch.delenv("SAKTHAI_EVAL_LOG", raising=False)
        result = config.eval_log_path()
        assert result.name == "eval.jsonl"
        assert result.parent == config.sakthai_home()

    def test_tilde_in_override_is_literal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The function takes the env value directly as Path(), which does not expand ~
        # Callers who want expansion must set the env var with ~ expanded
        monkeypatch.setenv("SAKTHAI_EVAL_LOG", "~/my_evals/eval.jsonl")
        result = config.eval_log_path()
        assert result == Path("~/my_evals/eval.jsonl")
