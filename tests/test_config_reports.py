"""Tests for the reporting helpers in sakthai.config.

Complements the basic path/structure checks in test_cycle_skills_config.py by
exercising the memory counts, env-var flags, and readiness logic that back
``sakthai doctor`` / ``sakthai status``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai import config
from sakthai.memory.store import MemoryStore


def test_sessions_dir_honours_home(sakthai_home: Path) -> None:
    assert config.sessions_dir() == sakthai_home / "sessions"


def test_mcp_timeout_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_TIMEOUT", raising=False)
    assert config.mcp_timeout() == config.DEFAULT_MCP_TIMEOUT


def test_mcp_timeout_honours_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_TIMEOUT", "45")
    assert config.mcp_timeout() == 45.0


@pytest.mark.parametrize("bad", ["", "abc", "0", "-5"])
def test_mcp_timeout_falls_back_on_bad_value(monkeypatch: pytest.MonkeyPatch, bad: str) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_TIMEOUT", bad)
    assert config.mcp_timeout() == config.DEFAULT_MCP_TIMEOUT


def test_ollama_host_default_is_ipv4(monkeypatch: pytest.MonkeyPatch) -> None:
    # Must be the 127.0.0.1 literal, not ``localhost``: on hosts where localhost
    # resolves to IPv6 ``::1`` and Ollama binds IPv4 only, a localhost default
    # fails with ``[Errno 111] Connection refused`` though the server is up.
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert config.ollama_host() == "http://127.0.0.1:11434"


def test_ollama_host_honours_env_and_strips_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://my-ollama:1234/")
    assert config.ollama_host() == "http://my-ollama:1234"


def test_memory_report_counts(sakthai_home: Path) -> None:
    with MemoryStore() as store:
        store.add_fact("one")
        store.add_fact("two")
        store.add_observation("an observation")

    report = config.check_env()
    mem = report["memory"]
    assert mem["db_exists"] is True
    assert mem["db_writable"] is True
    assert mem["fact_count"] == 2
    assert mem["observation_count"] == 1
    assert report["ready"] is True


def test_ready_true_when_db_absent(sakthai_home: Path) -> None:
    report = config.check_env()
    assert report["memory"]["db_exists"] is False
    assert report["ready"] is True


def test_env_report_flags(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("SAKTHAI_READ_ALLOW", raising=False)

    env = config.check_env()["env"]
    assert env["ANTHROPIC_API_KEY"]["set"] is True
    assert env["ANTHROPIC_API_KEY"]["required"] is True
    assert env["SAKTHAI_READ_ALLOW"]["set"] is False
    assert env["SAKTHAI_READ_ALLOW"]["required"] is False
