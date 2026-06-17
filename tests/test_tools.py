"""Tests for the built-in tool registry and handlers."""

from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from pathlib import Path

import pytest

import sakthai.agent.tools as _tools_mod
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


# -- _run_command error paths --------------------------------------------


def test_run_command_timeout(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    def _fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 30))

    monkeypatch.setattr(subprocess, "run", _fake_run)
    out = tool_by_name("run_command").handler({"command": "sleep 999"}, store)
    assert "[timeout" in out
    assert "sleep 999" in out


def test_run_command_oserror_raises_runtime(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    def _fake_run(cmd, **kwargs):
        raise OSError("No such file")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    with pytest.raises(RuntimeError, match="Failed to run command"):
        tool_by_name("run_command").handler({"command": "no_such_binary"}, store)


def test_run_command_truncates_large_output(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    big = "x" * (_tools_mod.MAX_CMD_OUTPUT_CHARS + 200)

    class _FakeProc:
        returncode = 0
        stdout = big
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeProc())
    out = tool_by_name("run_command").handler({"command": "echo big"}, store)
    assert "[truncated]" in out


def test_run_command_stderr_appended(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    class _FakeProc:
        returncode = 1
        stdout = ""
        stderr = "something went wrong"

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeProc())
    out = tool_by_name("run_command").handler({"command": "bad_cmd"}, store)
    assert "[stderr]" in out
    assert "something went wrong" in out
    assert "[exit 1]" in out


def test_run_command_invalid_timeout_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch, store
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    captured: dict = {}

    class _FakeProc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def _fake_run(cmd, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    tool_by_name("run_command").handler({"command": "echo ok", "timeout": "not-a-number"}, store)
    assert captured["timeout"] == _tools_mod._CMD_TIMEOUT_DEFAULT


# -- _send_telegram_message error paths ---------------------------------


def test_send_telegram_http_error(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    exc = urllib.error.HTTPError("https://api.telegram.org", 401, "Unauthorized", None, None)
    exc.read = lambda: b'{"description": "Unauthorized"}'  # type: ignore[method-assign]

    def _raise(_req, timeout=None):
        raise exc

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    out = tool_by_name("send_telegram_message").handler({"message": "test"}, store)
    assert "Telegram API Error" in out
    assert "Unauthorized" in out


def test_send_telegram_url_error(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    def _raise(_req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)
    out = tool_by_name("send_telegram_message").handler({"message": "test"}, store)
    assert "Network Error" in out
    assert "connection refused" in out


# -- _read_file edge cases -----------------------------------------------


def test_read_file_truncates_large_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    monkeypatch.chdir(tmp_path)
    big = "x" * (_tools_mod.MAX_FILE_READ_CHARS + 200)
    (tmp_path / "big.txt").write_text(big, encoding="utf-8")
    out = tool_by_name("read_file").handler({"path": "big.txt"}, store)
    assert "[truncated]" in out
    # The content portion before the truncation marker must not exceed the cap.
    content_part = out.replace("\n... [truncated]", "")
    assert len(content_part) <= _tools_mod.MAX_FILE_READ_CHARS


def test_read_file_sakthai_read_allow(
    tmp_path: Path, sakthai_home: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    # Create a file outside of cwd and sakthai_home.
    allowed_dir = tmp_path / "extra"
    allowed_dir.mkdir()
    target = allowed_dir / "data.txt"
    target.write_text("from allowed path", encoding="utf-8")

    # Without the env var the path is outside all permitted roots.
    with pytest.raises(PermissionError):
        tool_by_name("read_file").handler({"path": str(target)}, store)

    # Adding the directory to SAKTHAI_READ_ALLOW permits the read.
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(allowed_dir))
    out = tool_by_name("read_file").handler({"path": str(target)}, store)
    assert out == "from allowed path"


def test_read_file_requires_path(store) -> None:
    with pytest.raises(ValueError, match="`path` is required"):
        tool_by_name("read_file").handler({"path": ""}, store)


def test_read_file_missing_file_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        tool_by_name("read_file").handler({"path": "does_not_exist.txt"}, store)


def test_read_file_directory_is_not_a_regular_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    monkeypatch.chdir(tmp_path)
    sub = tmp_path / "adir"
    sub.mkdir()
    with pytest.raises(FileNotFoundError, match="is not a regular file"):
        tool_by_name("read_file").handler({"path": "adir"}, store)


def test_read_file_oserror_on_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store
) -> None:
    # Treating a regular file as a directory makes resolve() raise an OSError
    # subclass (NotADirectoryError), which must be surfaced as FileNotFoundError.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "file.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="could not be opened|is not a regular file"):
        tool_by_name("read_file").handler({"path": "file.txt/inner"}, store)


# -- input validation on the memory handlers -----------------------------


def test_run_command_requires_command(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    with pytest.raises(ValueError, match="`command` is required"):
        tool_by_name("run_command").handler({"command": "   "}, store)


def test_telegram_requires_message(store) -> None:
    with pytest.raises(ValueError, match="`message` is required"):
        tool_by_name("send_telegram_message").handler({"message": "  "}, store)


def test_search_requires_query(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`query` is required"):
        tool_by_name("search").handler({"query": ""}, store)


def test_forget_requires_fact_id(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`fact_id` is required"):
        tool_by_name("forget").handler({}, store)


def test_forget_rejects_non_numeric_string(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`fact_id` is required"):
        tool_by_name("forget").handler({"fact_id": "abc"}, store)


def test_forget_unknown_id_reports_missing(store: MemoryStore) -> None:
    out = tool_by_name("forget").handler({"fact_id": 999}, store)
    assert "No fact with id=999" in out


def test_recall_invalid_limit_falls_back_to_default(store: MemoryStore) -> None:
    # A non-numeric limit must not raise; it falls back to the default.
    tool_by_name("learn").handler({"value": "uses vim"}, store)
    out = tool_by_name("recall").handler({"limit": "not-a-number"}, store)
    assert "uses vim" in out


def test_recall_and_search_render_observations(store: MemoryStore) -> None:
    store.add_observation("prefers concise answers", weight=0.9)
    recalled = tool_by_name("recall").handler({}, store)
    assert "Observations:" in recalled
    assert "prefers concise answers" in recalled

    searched = tool_by_name("search").handler({"query": "concise"}, store)
    assert "Matching Observations" in searched
    assert "prefers concise answers" in searched


# -- _send_telegram_message success and remaining error paths -------------


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


def test_send_telegram_success(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda _req, timeout=None: _FakeResponse(b'{"ok": true}'),
    )
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "sent successfully" in out


def test_send_telegram_api_reports_not_ok(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda _req, timeout=None: _FakeResponse(b'{"ok": false, "description": "blocked"}'),
    )
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "Telegram send failed" in out
    assert "blocked" in out


def test_send_telegram_http_error_unparseable_body(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    exc = urllib.error.HTTPError("https://api.telegram.org", 500, "Server Error", None, None)
    exc.read = lambda: b"not json"  # type: ignore[method-assign]
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda _req, timeout=None: (_ for _ in ()).throw(exc),
    )
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "Telegram API HTTP Error 500" in out


def test_send_telegram_unexpected_error(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")

    def _boom(_req, timeout=None):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "Unexpected Error" in out
    assert "kaboom" in out


# -- _run_agent_loop ------------------------------------------------------


def test_run_agent_loop_rejects_recursion(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("SAKTHAI_AGENT_ACTIVE", "1")
    with pytest.raises(ValueError, match="Indirect recursion"):
        tool_by_name("run_agent_loop").handler({"task": "do it"}, store)


def test_run_agent_loop_requires_task(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.delenv("SAKTHAI_AGENT_ACTIVE", raising=False)
    with pytest.raises(ValueError, match="`task` is required"):
        tool_by_name("run_agent_loop").handler({"task": "  "}, store)


def test_run_agent_loop_prunes_history_by_default(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.delenv("SAKTHAI_AGENT_ACTIVE", raising=False)
    captured: dict = {}

    class _Result:
        text = "final answer"
        tool_calls: list = []

    def _fake_run_agent(**kwargs):
        captured.update(kwargs)
        return _Result()

    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "run_agent", _fake_run_agent)
    out = tool_by_name("run_agent_loop").handler(
        {"task": "summarize", "model": "claude-x", "provider": "anthropic", "max_iterations": "3"},
        store,
    )
    assert out == "final answer"
    assert captured["task"] == "summarize"
    assert captured["model"] == "claude-x"
    assert captured["provider"] == "anthropic"
    assert captured["max_iterations"] == 3
    # The nested loop must not be able to call itself.
    assert all(t.name != "run_agent_loop" for t in captured["tools"])


def test_run_agent_loop_can_return_tool_call_trace(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.delenv("SAKTHAI_AGENT_ACTIVE", raising=False)

    class _Result:
        text = "done"
        tool_calls = [{"name": "recall", "input": {}, "is_error": False}]

    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "run_agent", lambda **kw: _Result())
    out = tool_by_name("run_agent_loop").handler({"task": "x", "prune_history": False}, store)
    assert "Tool calls made in this loop:" in out
    assert "recall" in out


def test_run_agent_loop_non_bool_prune_history_defaults_to_true(
    monkeypatch: pytest.MonkeyPatch, store
) -> None:
    monkeypatch.delenv("SAKTHAI_AGENT_ACTIVE", raising=False)

    class _Result:
        text = "done"
        tool_calls: list = []

    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "run_agent", lambda **kw: _Result())
    # A non-bool prune_history is coerced to True, so only the result text returns.
    out = tool_by_name("run_agent_loop").handler({"task": "x", "prune_history": "yes"}, store)
    assert out == "done"
