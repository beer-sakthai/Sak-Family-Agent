"""Comprehensive diagnostic tests for check_env."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from sakthai import config


def test_check_env_all_defined_vars(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    """Ensure every env var in config.py is reported."""
    all_vars = {**config.REQUIRED_ENV_VARS, **config.OPTIONAL_ENV_VARS}

    # First, test with all unset
    for name in all_vars:
        monkeypatch.delenv(name, raising=False)

    report = config.check_env()
    env_report = report["env"]

    for name, desc in all_vars.items():
        assert name in env_report
        assert env_report[name]["set"] is False
        assert env_report[name]["required"] == (name in config.REQUIRED_ENV_VARS)
        assert env_report[name]["description"] == desc

    # Then, test with all set
    for name in all_vars:
        monkeypatch.setenv(name, "value")

    report = config.check_env()
    env_report = report["env"]

    for name in all_vars:
        assert env_report[name]["set"] is True


def test_auth_report_priority(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sakthai_home: Path
) -> None:
    """Test priority and all labels in auth report."""
    # Setup mock files for CLI tokens
    claude_dir = tmp_path / "claude"
    claude_dir.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude_dir))
    (claude_dir / ".credentials.json").write_text(
        '{"claudeAiOauth": {"accessToken": "t1", "expiresAt": 0}}'
    )

    # Default should be claude_cli if env vars are unset
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)

    report = config.check_env()["auth"]
    assert report["anthropic_source"] == "claude_cli"
    assert report["anthropic_ok"] is True

    # ANTHROPIC_AUTH_TOKEN overrides claude_cli
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "t2")
    report = config.check_env()["auth"]
    assert report["anthropic_source"] == "auth_token"

    # ANTHROPIC_API_KEY overrides both
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-1")
    report = config.check_env()["auth"]
    assert report["anthropic_source"] == "api_key"


def test_auth_report_openai_priority(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    """Test priority for OpenAI credential source."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)

    # 1. Ollama host
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    report = config.check_env()["auth"]
    assert report["openai_source"] == "ollama_host"
    assert report["openai_ok"] is True

    # 2. OpenAI API Base overrides Ollama host
    monkeypatch.setenv("OPENAI_API_BASE", "http://api-base")
    report = config.check_env()["auth"]
    assert report["openai_source"] == "openai_api_base"

    # 3. OpenAI API Key overrides others
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    report = config.check_env()["auth"]
    assert report["openai_source"] == "openai_api_key"


def test_ready_flag_combinations(
    monkeypatch: pytest.MonkeyPatch, sakthai_home: Path
) -> None:
    """Test the ready flag across multiple failure/success states."""
    # Ready if DB doesn't exist
    db_path = config.memory_db_path()
    if db_path.exists():
        db_path.unlink()
    assert config.check_env()["ready"] is True

    # Ready if DB exists and is writable
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("CREATE TABLE facts (fact TEXT)")
        conn.execute("CREATE TABLE observations (observation TEXT)")
    assert config.check_env()["ready"] is True

    # NOT ready if DB exists but is not writable
    original_access = os.access

    def mocked_access(path: Any, mode: int) -> bool:
        if str(path) == str(db_path) and mode == os.W_OK:
            return False
        return original_access(path, mode)

    monkeypatch.setattr(os, "access", mocked_access)
    assert config.check_env()["ready"] is False


def test_paths_report_with_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ensure path reporting respects SAKTHAI_HOME override."""
    custom_home = tmp_path / "custom_sakthai"
    monkeypatch.setenv("SAKTHAI_HOME", str(custom_home))

    report = config.check_env()["paths"]
    assert report["sakthai_home"] == str(custom_home)
    assert report["sakthai_home_exists"] is False  # Directory doesn't exist yet
    assert report["memory_db"] == str(custom_home / "memory.db")

    custom_home.mkdir()
    report = config.check_env()["paths"]
    assert report["sakthai_home_exists"] is True
