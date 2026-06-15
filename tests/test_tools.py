"""Tests for the built-in tool registry and handlers."""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.agent.tools import BUILTIN_TOOLS, tool_by_name
from sakthai.memory.store import MemoryStore


def test_registry_names_unique_and_schemas_valid() -> None:
    names = [t.name for t in BUILTIN_TOOLS]
    assert len(names) == len(set(names))
    for tool in BUILTIN_TOOLS:
        schema = tool.schema()
        assert schema["name"] == tool.name
        assert schema["input_schema"]["type"] == "object"


def test_tool_by_name() -> None:
    assert tool_by_name("learn").name == "learn"
    assert tool_by_name("nope") is None


def test_learn_recall_search_forget(store: MemoryStore) -> None:
    learn = tool_by_name("learn").handler
    recall = tool_by_name("recall").handler
    search = tool_by_name("search").handler
    forget = tool_by_name("forget").handler

    out = learn({"value": "uses vim", "kind": "pref"}, store)
    assert "Stored fact id=1" in out
    assert "uses vim" in recall({}, store)
    assert "uses vim" in search({"query": "vim"}, store)
    assert "No matches" in search({"query": "zzz"}, store)
    assert "Forgot fact id=1" in forget({"fact_id": 1}, store)
    assert "Memory is empty" in recall({}, store)


def test_learn_requires_value(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        tool_by_name("learn").handler({"value": "  "}, store)


def test_forget_rejects_non_int(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        tool_by_name("forget").handler({"fact_id": True}, store)


def test_read_file_within_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "note.txt"
    target.write_text("hello", encoding="utf-8")
    out = tool_by_name("read_file").handler({"path": "note.txt"}, store)
    assert out == "hello"


def test_read_file_blocks_outside_roots(tmp_path: Path, store) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("x", encoding="utf-8")
    with pytest.raises(PermissionError):
        tool_by_name("read_file").handler({"path": str(secret)}, store)


def test_run_command_disabled_by_default(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    with pytest.raises(PermissionError):
        tool_by_name("run_command").handler({"command": "echo hi"}, store)


def test_run_command_when_enabled(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    out = tool_by_name("run_command").handler({"command": "echo hello"}, store)
    assert "[exit 0]" in out
    assert "hello" in out


def test_telegram_missing_config(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "configuration missing" in out
