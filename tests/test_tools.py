"""Tests for the built-in tool registry and handlers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import sakthai.agent.tools as _tools_mod
from sakthai.agent.tools import (
    BUILTIN_TOOLS,
    _allowed_read_roots,
    _coerce_limit,
    _path_under_any_root,
    tool_by_name,
)
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


def test_ingest_document_parses_common_formats(tmp_path: Path, store: MemoryStore) -> None:
    ingest = tool_by_name("ingest_document")
    assert ingest is not None

    markdown = tmp_path / "price-book.md"
    markdown.write_text(
        "# Price book\n\n- Website audit: $250\n- Support plan: $99/month\n",
        encoding="utf-8",
    )
    csv_file = tmp_path / "faq.csv"
    csv_file.write_text(
        "question,answer\nHow long does setup take?,2 business days\nDo you offer support?,Yes\n",
        encoding="utf-8",
    )
    plain_text = tmp_path / "notes.txt"
    plain_text.write_text("Custom project quotes are scoped after discovery.", encoding="utf-8")

    out_md = ingest.handler({"path": str(markdown)}, store)
    out_csv = ingest.handler({"path": str(csv_file)}, store)
    out_txt = ingest.handler({"path": str(plain_text)}, store)

    assert "learned" in out_md
    assert "learned" in out_csv
    assert "learned" in out_txt

    facts = store.list_facts()
    assert len(facts) == 5
    assert {f.kind for f in facts} == {"fact"}
    assert {f.value for f in facts} == {
        "Website audit: $250",
        "Support plan: $99/month",
        "How long does setup take? -> 2 business days",
        "Do you offer support? -> Yes",
        "Custom project quotes are scoped after discovery.",
    }


def test_capture_lead_stores_structured_contact_details(store: MemoryStore) -> None:
    capture_lead = tool_by_name("capture_lead")
    assert capture_lead is not None

    out = capture_lead.handler(
        {
            "name": "Ada",
            "phone": "+1-555-0100",
            "email": "ada@example.com",
            "query": "Need a quote for a website refresh",
        },
        store,
    )

    assert "captured" in out
    facts = store.list_facts()
    assert len(facts) == 1
    lead = facts[0]
    assert lead.kind == "lead"
    assert lead.key == "Ada"
    assert json.loads(lead.value) == {
        "name": "Ada",
        "phone": "+1-555-0100",
        "email": "ada@example.com",
        "query": "Need a quote for a website refresh",
    }


def test_learn_requires_value(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        tool_by_name("learn").handler({"value": "  "}, store)


def test_forget_rejects_non_int(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`fact_id` is required and must be an integer."):
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
    from unittest.mock import MagicMock

    mock_run = MagicMock()
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "hello output"
    mock_run.return_value.stderr = ""
    monkeypatch.setattr("subprocess.run", mock_run)
    out = tool_by_name("run_command").handler({"command": "some command"}, store)
    assert "[exit 0]" in out
    assert "hello output" in out


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
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
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
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
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
    with pytest.raises(ValueError, match="`fact_id` is required and must be an integer."):
        tool_by_name("forget").handler({}, store)


def test_forget_rejects_non_numeric_string(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`fact_id` is required and must be an integer."):
        tool_by_name("forget").handler({"fact_id": "abc"}, store)


def test_forget_rejects_invalid_type(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="`fact_id` is required and must be an integer."):
        tool_by_name("forget").handler({"fact_id": [1, 2]}, store)


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
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda _req, timeout=None: _FakeResponse(b'{"ok": true}'),
    )
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "sent successfully" in out


def test_send_telegram_api_reports_not_ok(monkeypatch: pytest.MonkeyPatch, store) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
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
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
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
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:fake-token")
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


# ---------------------------------------------------------------------------
# _path_under_any_root — unit tests for the private sandbox helper
# ---------------------------------------------------------------------------


class TestPathUnderAnyRoot:
    def test_exact_root_match(self, tmp_path: Path) -> None:
        assert _path_under_any_root(tmp_path, [tmp_path])

    def test_subdirectory_allowed(self, tmp_path: Path) -> None:
        sub = tmp_path / "a" / "b"
        sub.mkdir(parents=True)
        assert _path_under_any_root(sub, [tmp_path])

    def test_sibling_directory_rejected(self, tmp_path: Path) -> None:
        root = tmp_path / "root"
        sibling = tmp_path / "other"
        root.mkdir()
        assert not _path_under_any_root(sibling, [root])

    def test_empty_roots_always_returns_false(self, tmp_path: Path) -> None:
        assert not _path_under_any_root(tmp_path, [])

    def test_multiple_roots_first_match_wins(self, tmp_path: Path) -> None:
        root_a = tmp_path / "a"
        root_b = tmp_path / "b"
        target = tmp_path / "b" / "file.txt"
        root_a.mkdir()
        root_b.mkdir()
        target.write_text("x", encoding="utf-8")
        assert _path_under_any_root(target, [root_a, root_b])


# ---------------------------------------------------------------------------
# _allowed_read_roots — SAKTHAI_READ_ALLOW parsing
# ---------------------------------------------------------------------------


class TestAllowedReadRoots:
    def test_multiple_read_allow_paths_parsed(
        self, tmp_path: Path, sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dir_a = tmp_path / "allowed_a"
        dir_b = tmp_path / "allowed_b"
        dir_a.mkdir()
        dir_b.mkdir()
        monkeypatch.setenv("SAKTHAI_READ_ALLOW", os.pathsep.join([str(dir_a), str(dir_b)]))
        roots = _allowed_read_roots()
        assert dir_a.resolve() in roots
        assert dir_b.resolve() in roots

    def test_empty_tokens_in_read_allow_ignored(
        self, sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_READ_ALLOW", f"{os.pathsep}{os.pathsep}")
        roots = _allowed_read_roots()
        assert isinstance(roots, list)

    def test_read_file_respects_multiple_allow_paths(
        self,
        tmp_path: Path,
        sakthai_home: Path,
        monkeypatch: pytest.MonkeyPatch,
        store: MemoryStore,
    ) -> None:
        dir_a = tmp_path / "allowed_a"
        dir_b = tmp_path / "allowed_b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "file_a.txt").write_text("from a", encoding="utf-8")
        (dir_b / "file_b.txt").write_text("from b", encoding="utf-8")
        monkeypatch.setenv("SAKTHAI_READ_ALLOW", os.pathsep.join([str(dir_a), str(dir_b)]))
        assert (
            tool_by_name("read_file").handler({"path": str(dir_a / "file_a.txt")}, store)
            == "from a"
        )
        assert (
            tool_by_name("read_file").handler({"path": str(dir_b / "file_b.txt")}, store)
            == "from b"
        )


# ---------------------------------------------------------------------------
# read_file — error paths
# ---------------------------------------------------------------------------


class TestReadFileErrors:
    def test_read_file_non_existent_path(self, sakthai_home: Path, store: MemoryStore) -> None:
        with pytest.raises(FileNotFoundError, match="is not a regular file"):
            tool_by_name("read_file").handler({"path": "/non/existent/path/at/all"}, store)

    def test_read_file_oserror_on_resolve(
        self, sakthai_home: Path, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        original_resolve = Path.resolve

        def _patched_resolve(self, *args, **kwargs):
            if "simulated_os_error.txt" in str(self):
                raise OSError("simulated os error")
            return original_resolve(self, *args, **kwargs)

        monkeypatch.setattr(Path, "resolve", _patched_resolve)

        with pytest.raises(FileNotFoundError, match="could not be opened: simulated os error"):
            tool_by_name("read_file").handler({"path": "simulated_os_error.txt"}, store)


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows requires admin privileges for symlinks"
)
class TestReadFileSymlink:
    def test_symlink_to_outside_root_is_blocked(
        self,
        tmp_path: Path,
        sakthai_home: Path,
        monkeypatch: pytest.MonkeyPatch,
        store: MemoryStore,
    ) -> None:
        secret_dir = tmp_path / "secret"
        secret_dir.mkdir()
        secret = secret_dir / "secret.txt"
        secret.write_text("private", encoding="utf-8")
        cwd_dir = tmp_path / "working"
        cwd_dir.mkdir()
        link = cwd_dir / "link.txt"
        link.symlink_to(secret)
        monkeypatch.chdir(cwd_dir)
        # The symlink is in cwd, but it resolves to outside cwd and sakthai_home.
        with pytest.raises(PermissionError):
            tool_by_name("read_file").handler({"path": "link.txt"}, store)

    def test_symlink_within_root_is_allowed(
        self,
        tmp_path: Path,
        sakthai_home: Path,
        monkeypatch: pytest.MonkeyPatch,
        store: MemoryStore,
    ) -> None:
        monkeypatch.chdir(tmp_path)
        real_file = tmp_path / "real.txt"
        real_file.write_text("visible", encoding="utf-8")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)
        out = tool_by_name("read_file").handler({"path": "link.txt"}, store)
        assert out == "visible"


# ---------------------------------------------------------------------------
# run_command — timeout clamping
# ---------------------------------------------------------------------------


class TestRunCommandTimeoutClamping:
    def _capture_timeout(self, monkeypatch: pytest.MonkeyPatch) -> dict:
        captured: dict = {}

        class _FakeProc:
            returncode = 0
            stdout = "ok"
            stderr = ""

        def _fake_run(cmd: object, **kwargs: object) -> _FakeProc:
            captured["timeout"] = kwargs.get("timeout")
            return _FakeProc()

        monkeypatch.setattr(subprocess, "run", _fake_run)
        return captured

    def test_timeout_below_minimum_clamped_to_one(
        self, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
        captured = self._capture_timeout(monkeypatch)
        tool_by_name("run_command").handler({"command": "echo ok", "timeout": 0.1}, store)
        assert captured["timeout"] == 1.0

    def test_timeout_above_maximum_clamped(
        self, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
        captured = self._capture_timeout(monkeypatch)
        tool_by_name("run_command").handler({"command": "echo ok", "timeout": 99999}, store)
        assert captured["timeout"] == _tools_mod._CMD_TIMEOUT_MAX

    def test_timeout_within_range_passes_through(
        self, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
        captured = self._capture_timeout(monkeypatch)
        tool_by_name("run_command").handler({"command": "echo ok", "timeout": 45}, store)
        assert captured["timeout"] == 45.0


# ---------------------------------------------------------------------------
# send_telegram_message — partial environment configuration
# ---------------------------------------------------------------------------


class TestSendTelegramPartialConfig:
    def test_only_token_set_returns_config_missing(
        self, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "12345:my-token")
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
        assert "configuration missing" in out

    def test_only_chat_id_set_returns_config_missing(
        self, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
    ) -> None:
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456")
        out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
        assert "configuration missing" in out


# ---------------------------------------------------------------------------
# run_command — output edge cases
# ---------------------------------------------------------------------------


def test_run_command_no_output_returns_exit_tag_only(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    """A command that produces no stdout and no stderr returns just '[exit 0]'."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    class _Silent:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _Silent())
    out = tool_by_name("run_command").handler({"command": "silent_cmd"}, store)
    assert out == "[exit 0]"


def test_run_command_empty_shell_allow_is_disabled(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    """SAKTHAI_SHELL_ALLOW='' (empty string) is falsy and must keep the tool disabled."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "")
    with pytest.raises(PermissionError):
        tool_by_name("run_command").handler({"command": "echo hi"}, store)


# ---------------------------------------------------------------------------
# _allowed_read_roots and _path_under_any_root error paths
# ---------------------------------------------------------------------------


def test_allowed_read_roots_skips_oserror_on_sakthai_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OSError from sakthai_home().resolve() is silently skipped."""
    bad = MagicMock(spec=Path)
    bad.resolve.side_effect = OSError("permission denied")
    monkeypatch.setattr(_tools_mod, "sakthai_home", lambda: bad)
    roots = _allowed_read_roots()
    # sakthai_home was skipped; cwd should still appear
    assert isinstance(roots, list)
    assert len(roots) >= 1


def test_allowed_read_roots_skips_oserror_on_allow_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OSError from Path(token).expanduser().resolve() in SAKTHAI_READ_ALLOW is skipped."""
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", "/some/bad/path")

    original_resolve = Path.resolve

    def _patched_resolve(self: Path, *a: object, **kw: object) -> Path:
        if "bad" in str(self):
            raise OSError("unresolvable path")
        return original_resolve(self, *a, **kw)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "resolve", _patched_resolve)
    roots = _allowed_read_roots()
    assert isinstance(roots, list)
    assert all("bad" not in str(r) for r in roots)


def test_path_under_any_root_skips_oserror_and_valueerror() -> None:
    """ValueError and OSError from is_relative_to are silently skipped."""
    bad_root: MagicMock = MagicMock(spec=Path)
    bad_root.__eq__ = lambda self, other: False
    bad_root.is_relative_to.side_effect = ValueError("incompatible")
    assert _path_under_any_root(Path("/some/path"), [bad_root]) is False

    bad_root.is_relative_to.side_effect = OSError("permission denied")
    assert _path_under_any_root(Path("/some/path"), [bad_root]) is False


def test_path_under_any_root_oserror_on_real_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkeypatch Path.is_relative_to to raise OSError on the *caller* side.

    The existing test above sets side_effect on the mock *root*, but
    _path_under_any_root calls path.is_relative_to(root) — the real Path
    method on the subject path, not on root.  This test exercises the
    except branch correctly.
    """

    def _raise_oserror(self: Path, *args: object, **kwargs: object) -> bool:
        raise OSError("simulated filesystem error in is_relative_to")

    monkeypatch.setattr(Path, "is_relative_to", _raise_oserror)
    assert _path_under_any_root(Path("/some/path"), [Path("/root")]) is False


# -- behaviour assertions that close mutation-testing gaps ----------------
# The following pin exact behaviour that mutation testing (mutmut) found
# unasserted: surviving mutants in _coerce_limit, _read_file, and _run_command
# that line coverage alone did not catch. Each test would fail if its named
# behaviour were silently changed.


def test_coerce_limit_clamps_to_floor_of_one() -> None:
    # A negative request must clamp to 1, not pass through and not floor at 2.
    assert _coerce_limit("-5", 20) == 1
    assert _coerce_limit(-1, 20) == 1
    # Falsy input falls back to the default (0 is falsy → default, not int(0)).
    assert _coerce_limit(0, 20) == 20
    assert _coerce_limit(None, 50) == 50
    # Over-cap requests clamp to the max.
    assert _coerce_limit(10_000, 20) == 200


def test_read_file_outside_roots_message_names_allow_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A blocked read must explain *why* and name the escape hatch, not raise a
    # bare PermissionError. (No chdir, so this test participates in mutmut.)
    monkeypatch.delenv("SAKTHAI_READ_ALLOW", raising=False)
    secret = tmp_path / "outside.txt"
    secret.write_text("top secret", encoding="utf-8")
    with pytest.raises(PermissionError, match="outside the allowed roots"):
        tool_by_name("read_file").handler({"path": str(secret)}, MemoryStore(":memory:"))
    with pytest.raises(PermissionError, match="SAKTHAI_READ_ALLOW"):
        tool_by_name("read_file").handler({"path": str(secret)}, MemoryStore(":memory:"))


def test_read_file_decodes_invalid_utf8_with_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # errors="replace" must let undecodable bytes through as U+FFFD rather than
    # raising UnicodeDecodeError (errors=None/"strict" would blow up).
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))
    f = tmp_path / "bad.bin"
    f.write_bytes(b"good\xff\xfetail")
    out = tool_by_name("read_file").handler({"path": str(f)}, MemoryStore(":memory:"))
    assert "good" in out and "tail" in out
    assert "�" in out  # replacement character, not an exception


def test_run_command_disabled_message_is_explicit(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    with pytest.raises(PermissionError, match="Shell execution is disabled"):
        tool_by_name("run_command").handler({"command": "echo hi"}, store)


def test_run_command_stderr_separator_when_stdout_present(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    # When stdout is non-empty, stderr must be joined with a leading newline and
    # the lowercase "[stderr]" marker (the empty-stdout branch is covered
    # elsewhere; this pins the with-stdout branch).
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")

    class _FakeProc:
        returncode = 2
        stdout = "out-line"
        stderr = "err-line"

    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeProc())
    out = tool_by_name("run_command").handler({"command": "whatever"}, store)
    assert "out-line\n[stderr]\nerr-line" in out
    assert "[exit 2]" in out


def test_send_telegram_invalid_token_format(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "not-a-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    out = tool_by_name("send_telegram_message").handler({"message": "hi"}, store)
    assert "Invalid TELEGRAM_BOT_TOKEN format" in out
