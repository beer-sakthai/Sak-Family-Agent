"""Tests for the 4 first-class workspace coding tools: edit_file, write_file, grep_search, glob_files."""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.agent.chat import format_diff_renderable, tool_args_summary
from sakthai.agent.tools import (
    BUILTIN_TOOLS,
    build_file_diff_preview,
    tool_by_name,
)
from sakthai.memory.store import MemoryStore


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore(":memory:")


@pytest.fixture(autouse=True)
def _allow_tmp_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_WRITE_ALLOW", str(tmp_path))
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))


def test_coding_tools_registered_in_builtin_tools() -> None:
    names = {t.name for t in BUILTIN_TOOLS}
    assert {"edit_file", "write_file", "grep_search", "glob_files"} <= names

    edit_tool = tool_by_name("edit_file")
    assert edit_tool is not None
    assert edit_tool.requires_confirmation is True

    write_tool = tool_by_name("write_file")
    assert write_tool is not None
    assert write_tool.requires_confirmation is True

    grep_tool = tool_by_name("grep_search")
    assert grep_tool is not None
    assert grep_tool.requires_confirmation is False

    glob_tool = tool_by_name("glob_files")
    assert glob_tool is not None
    assert glob_tool.requires_confirmation is False


def test_write_file_creates_and_overwrites(tmp_path: Path, store: MemoryStore) -> None:
    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    target = tmp_path / "subdir" / "hello.py"
    res = write_tool.handler(
        {"path": str(target), "content": "print('hello world')\n", "create_dirs": True},
        store,
    )
    assert "Created" in res
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == "print('hello world')\n"

    res_update = write_tool.handler(
        {"path": str(target), "content": "print('updated')\n"},
        store,
    )
    assert "Updated" in res_update
    assert target.read_text(encoding="utf-8") == "print('updated')\n"


def test_write_file_no_create_dirs_raises_error(tmp_path: Path, store: MemoryStore) -> None:
    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    target = tmp_path / "nonexistent" / "file.txt"
    with pytest.raises(FileNotFoundError, match="Parent directory"):
        write_tool.handler({"path": str(target), "content": "data", "create_dirs": False}, store)


def test_write_file_blocks_sensitive_and_outside_roots(
    tmp_path: Path, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    # Block sensitive .env
    with pytest.raises(PermissionError, match="sensitive or protected"):
        write_tool.handler({"path": ".env", "content": "SECRET=123"}, store)

    with pytest.raises(PermissionError, match="sensitive or protected"):
        write_tool.handler({"path": ".git/hooks/pre-commit", "content": "#!/bin/sh"}, store)

    # Block outside allowed roots
    outside = Path("/tmp/outside_sakthai_test_file.txt")  # nosec B108
    with pytest.raises(PermissionError, match="outside the allowed write roots"):
        write_tool.handler({"path": str(outside), "content": "data"}, store)


def test_edit_file_unique_replacement(tmp_path: Path, store: MemoryStore) -> None:
    edit_tool = tool_by_name("edit_file")
    assert edit_tool is not None

    target = tmp_path / "app.py"
    target.write_text("def run():\n    return 42\n", encoding="utf-8")

    out = edit_tool.handler(
        {
            "path": str(target),
            "old_text": "    return 42",
            "new_text": "    return 100",
        },
        store,
    )
    assert "Edited" in out
    assert "+1 / -1 lines" in out
    assert target.read_text(encoding="utf-8") == "def run():\n    return 100\n"


def test_edit_file_old_text_not_found(tmp_path: Path, store: MemoryStore) -> None:
    edit_tool = tool_by_name("edit_file")
    assert edit_tool is not None

    target = tmp_path / "app.py"
    target.write_text("def run():\n    return 42\n", encoding="utf-8")

    with pytest.raises(ValueError, match="`old_text` was not found"):
        edit_tool.handler(
            {
                "path": str(target),
                "old_text": "non_existent_text",
                "new_text": "something",
            },
            store,
        )


def test_edit_file_multiple_matches_error_and_replace_all(
    tmp_path: Path, store: MemoryStore
) -> None:
    edit_tool = tool_by_name("edit_file")
    assert edit_tool is not None

    target = tmp_path / "items.py"
    target.write_text("item = 1\nitem = 1\nitem = 1\n", encoding="utf-8")

    # Error without replace_all=True
    with pytest.raises(ValueError, match="matched 3 locations"):
        edit_tool.handler(
            {
                "path": str(target),
                "old_text": "item = 1",
                "new_text": "item = 2",
            },
            store,
        )

    # Success with replace_all=True
    out = edit_tool.handler(
        {
            "path": str(target),
            "old_text": "item = 1",
            "new_text": "item = 2",
            "replace_all": True,
        },
        store,
    )
    assert "3 replacements" in out
    assert target.read_text(encoding="utf-8") == "item = 2\nitem = 2\nitem = 2\n"


def test_build_file_diff_preview(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("hello\nworld\n", encoding="utf-8")

    diff_text, added, removed = build_file_diff_preview(
        "edit_file",
        {"path": str(target), "old_text": "world", "new_text": "universe"},
    )
    assert "-world" in diff_text
    assert "+universe" in diff_text
    assert added == 1
    assert removed == 1

    # write_file diff
    diff_text_w, added_w, removed_w = build_file_diff_preview(
        "write_file",
        {"path": str(target), "content": "brand new content\n"},
    )
    assert "+brand new content" in diff_text_w
    assert added_w >= 1
    assert removed_w >= 1


def test_grep_search_and_glob_files(tmp_path: Path, store: MemoryStore) -> None:
    grep_tool = tool_by_name("grep_search")
    glob_tool = tool_by_name("glob_files")
    assert grep_tool is not None
    assert glob_tool is not None

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("def execute_order_66():\n    pass\n", encoding="utf-8")
    (src_dir / "utils.py").write_text("def helper():\n    pass\n", encoding="utf-8")

    # Ignore dir: node_modules
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / "vendor.js").write_text("execute_order_66()", encoding="utf-8")

    # Grep test
    res = grep_tool.handler(
        {"pattern": "execute_order_66", "path": str(tmp_path)},
        store,
    )
    assert "main.py:1: def execute_order_66():" in res
    assert "node_modules" not in res

    # Glob test
    glob_res = glob_tool.handler(
        {"pattern": "*.py", "path": str(tmp_path)},
        store,
    )
    assert "main.py" in glob_res
    assert "utils.py" in glob_res
    assert "node_modules" not in glob_res


def test_diff_formatting_and_args_summary() -> None:
    panel = format_diff_renderable(
        "--- a/foo\n+++ b/foo\n@@ -1 +1 @@\n-old\n+new\n",
        added=1,
        removed=1,
        path="foo",
    )
    assert panel.title is not None
    assert "foo" in str(panel.title)

    summary = tool_args_summary("edit_file", {"path": "test.py", "old_text": "x" * 50})
    assert "test.py" in summary
    assert "…" in summary


def test_is_sensitive_write_target_variants() -> None:
    from sakthai.agent.tools import _is_sensitive_write_target

    assert _is_sensitive_write_target(Path(".env-prod")) is True
    assert _is_sensitive_write_target(Path(".env_staging")) is True
    assert _is_sensitive_write_target(Path("memory.db-wal")) is True
    assert _is_sensitive_write_target(Path(".ssh/id_rsa")) is True
    assert _is_sensitive_write_target(Path(".git/config")) is True
    assert _is_sensitive_write_target(Path(".aws/credentials")) is True
    assert _is_sensitive_write_target(Path("src/normal_file.py")) is False


def test_resolve_and_validate_write_path_directory_and_missing(tmp_path: Path) -> None:
    from sakthai.agent.tools import _resolve_and_validate_write_path

    # Directory raises IsADirectoryError
    with pytest.raises(IsADirectoryError, match="is a directory"):
        _resolve_and_validate_write_path(str(tmp_path))

    # Missing file with must_exist=True raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        _resolve_and_validate_write_path(str(tmp_path / "absent.py"), must_exist=True)


def test_build_file_diff_preview_edge_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Empty path
    assert build_file_diff_preview("edit_file", {"path": ""}) == ("", 0, 0)
    # Non-diff tool
    assert build_file_diff_preview("other_tool", {"path": "test.py"}) == ("", 0, 0)
    # write_file with non-string content
    assert build_file_diff_preview("write_file", {"path": "test.py", "content": 123}) == ("", 0, 0)
    # edit_file with non-string old_text or new_text
    assert build_file_diff_preview(
        "edit_file", {"path": "test.py", "old_text": "", "new_text": "b"}
    ) == ("", 0, 0)
    assert build_file_diff_preview(
        "edit_file", {"path": "test.py", "old_text": "a", "new_text": 123}
    ) == ("", 0, 0)

    # edit_file where old_text is not found
    file = tmp_path / "foo.txt"
    file.write_text("hello world", encoding="utf-8")
    preview, a, r = build_file_diff_preview(
        "edit_file", {"path": str(file), "old_text": "nonexistent", "new_text": "b"}
    )
    assert "old_text not found" in preview
    assert a == 0 and r == 0

    # edit_file replace_all=True
    file2 = tmp_path / "bar.txt"
    file2.write_text("x x x", encoding="utf-8")
    diff, a2, r2 = build_file_diff_preview(
        "edit_file",
        {"path": str(file2), "old_text": "x", "new_text": "y", "replace_all": True},
    )
    assert "-x x x" in diff
    assert "+y y y" in diff

    # OSError on read returns empty old content
    monkeypatch.setattr(
        Path, "read_text", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("boom"))
    )
    diff_os, a3, r3 = build_file_diff_preview("write_file", {"path": str(file), "content": "fresh"})
    assert "+fresh" in diff_os


def test_edit_file_input_validation(tmp_path: Path, store: MemoryStore) -> None:
    edit_tool = tool_by_name("edit_file")
    assert edit_tool is not None

    with pytest.raises(ValueError, match="`path` is required"):
        edit_tool.handler({"path": "", "old_text": "a", "new_text": "b"}, store)

    with pytest.raises(ValueError, match="`old_text` is required"):
        edit_tool.handler(
            {"path": str(tmp_path / "test.py"), "old_text": "", "new_text": "b"}, store
        )

    with pytest.raises(ValueError, match="`new_text` is required"):
        edit_tool.handler(
            {"path": str(tmp_path / "test.py"), "old_text": "a", "new_text": 123}, store
        )

    # Target is directory
    with pytest.raises((IsADirectoryError, FileNotFoundError)):
        edit_tool.handler({"path": str(tmp_path), "old_text": "a", "new_text": "b"}, store)


def test_write_file_input_validation(tmp_path: Path, store: MemoryStore) -> None:
    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    with pytest.raises(ValueError, match="`path` is required"):
        write_tool.handler({"path": "", "content": "data"}, store)

    with pytest.raises(ValueError, match="`content` is required"):
        write_tool.handler({"path": str(tmp_path / "test.py"), "content": 123}, store)

    with pytest.raises(IsADirectoryError):
        write_tool.handler({"path": str(tmp_path), "content": "data"}, store)


def test_grep_search_options_and_errors(tmp_path: Path, store: MemoryStore) -> None:
    grep_tool = tool_by_name("grep_search")
    assert grep_tool is not None

    with pytest.raises(ValueError, match="`pattern` is required"):
        grep_tool.handler({"pattern": "", "path": str(tmp_path)}, store)

    with pytest.raises(ValueError, match="Invalid regular expression"):
        grep_tool.handler({"pattern": "[unclosed", "path": str(tmp_path)}, store)

    with pytest.raises(FileNotFoundError):
        grep_tool.handler({"pattern": "foo", "path": str(tmp_path / "missing_dir")}, store)

    file_a = tmp_path / "a.py"
    file_a.write_text("Hello Case\nHELLO case\n", encoding="utf-8")

    # Case insensitive via case_sensitive=False
    res_i = grep_tool.handler(
        {"pattern": "hello", "path": str(tmp_path), "case_sensitive": False}, store
    )
    assert "Hello Case" in res_i
    assert "HELLO case" in res_i

    # Max results truncation indicator
    res_trunc = grep_tool.handler(
        {"pattern": "case", "path": str(tmp_path), "max_results": 1, "case_sensitive": False},
        store,
    )
    assert "Matches (1+):" in res_trunc

    # No matches found
    res_none = grep_tool.handler({"pattern": "nomatch_anywhere", "path": str(tmp_path)}, store)
    assert "No matches found" in res_none

    # Skips unreadable/binary file
    bin_file = tmp_path / "binary.dat"
    bin_file.write_bytes(b"\x00\xff\xfe\x00")
    res_bin = grep_tool.handler(
        {"pattern": "case", "path": str(tmp_path), "case_sensitive": False}, store
    )
    assert "binary.dat" not in res_bin


def test_glob_files_options_and_errors(tmp_path: Path, store: MemoryStore) -> None:
    glob_tool = tool_by_name("glob_files")
    assert glob_tool is not None

    with pytest.raises(ValueError, match="`pattern` is required"):
        glob_tool.handler({"pattern": "", "path": str(tmp_path)}, store)

    with pytest.raises(FileNotFoundError):
        glob_tool.handler({"pattern": "*", "path": str(tmp_path / "missing_dir")}, store)

    (tmp_path / "file1.txt").write_text("1", encoding="utf-8")
    (tmp_path / "file2.txt").write_text("2", encoding="utf-8")

    # Max results truncation
    res_trunc = glob_tool.handler(
        {"pattern": "*.txt", "path": str(tmp_path), "max_results": 1}, store
    )
    assert "Matched files (1+):" in res_trunc

    # No files matched
    res_none = glob_tool.handler({"pattern": "*.nonexistent", "path": str(tmp_path)}, store)
    assert "No files matched pattern" in res_none


def test_tool_args_summary_all_cases() -> None:
    assert "10 chars" in tool_args_summary(
        "write_file", {"path": "test.txt", "content": "0123456789"}
    )
    assert "read.txt" in tool_args_summary("read_file", {"path": "read.txt"})
    assert "'python tips'" in tool_args_summary("web_search", {"query": "python tips"})
    assert "git status" in tool_args_summary("run_command", {"command": "git status"})
    assert "other" in tool_args_summary("other_tool", {"other": "val"})
    assert "raw_val" in tool_args_summary("other_tool", "raw_val")  # type: ignore[arg-type]


def test_cli_make_confirm_tool_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from rich.console import Console

    from sakthai.cli.chat import _make_confirm_tool

    target = tmp_path / "file.py"
    target.write_text("foo = 1\n", encoding="utf-8")

    # 'y' allows execution
    allowed_session: set[str] = set()
    confirm = _make_confirm_tool(session_allowed=allowed_session, persona="sakthai")

    monkeypatch.setattr(Console, "input", lambda *args, **kwargs: "y")
    assert confirm("edit_file", {"path": str(target), "old_text": "1", "new_text": "2"}) is True

    # 'n' denies execution
    monkeypatch.setattr(Console, "input", lambda *args, **kwargs: "n")
    assert confirm("write_file", {"path": str(target), "content": "foo = 3\n"}) is False

    # 'a' allows and adds to allowed_session
    monkeypatch.setattr(Console, "input", lambda *args, **kwargs: "a")
    assert confirm("write_file", {"path": str(target), "content": "foo = 4\n"}) is True
    assert "write_file" in allowed_session
    # Next call returns True immediately without prompting
    assert confirm("write_file", {"path": str(target), "content": "foo = 5\n"}) is True

    # Non-diff tool
    monkeypatch.setattr(Console, "input", lambda *args, **kwargs: "y")
    assert confirm("run_command", {"command": "echo 1"}) is True

    # EOFError denies
    def _raise_eof(*args: object, **kwargs: object) -> str:
        raise EOFError

    monkeypatch.setattr(Console, "input", _raise_eof)
    assert (
        confirm("edit_file", {"path": str(target), "old_text": "foo", "new_text": "bar"}) is False
    )


def test_loop_unattended_mode_guardrail(
    tmp_path: Path, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.agent.guardrails import GuardrailPolicy
    from sakthai.agent.loop import _execute_tool_with_guardrails

    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    target = "unattended.txt"
    policy = GuardrailPolicy(pre_rules=(), post_rules=())

    # When SAKTHAI_WRITE_ALLOW is unset and on_confirm is None, tool is denied
    monkeypatch.delenv("SAKTHAI_WRITE_ALLOW", raising=False)
    msg, is_err = _execute_tool_with_guardrails(
        write_tool,
        {"path": target, "content": "data"},
        store,
        policy=policy,
        on_confirm=None,
    )
    assert is_err is True
    assert "requires interactive confirmation or SAKTHAI_WRITE_ALLOW in unattended mode" in msg

    # When user denies via on_confirm
    msg_denied, is_err_denied = _execute_tool_with_guardrails(
        write_tool,
        {"path": target, "content": "data"},
        store,
        policy=policy,
        on_confirm=lambda name, args: False,
    )
    assert is_err_denied is True
    assert "denied by the user" in msg_denied


def test_iter_workspace_files_and_grep_branches(tmp_path: Path, store: MemoryStore) -> None:
    grep_tool = tool_by_name("grep_search")
    glob_tool = tool_by_name("glob_files")
    assert grep_tool is not None
    assert glob_tool is not None

    single_file = tmp_path / "single.py"
    single_file.write_text("prefix " + ("x" * 220) + " suffix\n", encoding="utf-8")

    # Grep on single file directly (root.is_file branch)
    res_single = grep_tool.handler({"pattern": "prefix", "path": str(single_file)}, store)
    assert "single.py:1:" in res_single
    assert "…" in res_single  # >200 chars snippet truncation

    # Grep with glob filter
    py_file = tmp_path / "code.py"
    py_file.write_text("target_function()\n", encoding="utf-8")
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("target_function()\n", encoding="utf-8")

    res_glob = grep_tool.handler(
        {"pattern": "target_function", "path": str(tmp_path), "glob": "*.py"},
        store,
    )
    assert "code.py" in res_glob
    assert "notes.txt" not in res_glob

    # Symlink skipping
    symlink_file = tmp_path / "symlink.py"
    try:
        symlink_file.symlink_to(py_file)
        res_sym = grep_tool.handler({"pattern": "target_function", "path": str(tmp_path)}, store)
        assert "symlink.py" not in res_sym
    except (OSError, NotImplementedError):
        pass

    # Glob on a file instead of directory raises ValueError
    with pytest.raises(ValueError, match="is not a directory"):
        glob_tool.handler({"pattern": "*.py", "path": str(single_file)}, store)


def test_write_file_parent_exists_and_diff_fallback(tmp_path: Path, store: MemoryStore) -> None:
    from sakthai.agent.tools import _compute_unified_diff

    write_tool = tool_by_name("write_file")
    assert write_tool is not None

    # Write when parent already exists
    target = tmp_path / "parent_exists.txt"
    out = write_tool.handler({"path": str(target), "content": "alpha\n"}, store)
    assert "Created" in out

    # Diff fallback when old != new but lines have no diff
    diff, a, r = _compute_unified_diff("abc", "xyz", "sample.txt")
    assert "@@ -1 +1 @@" in diff
    assert a >= 1 and r >= 1


def test_resolve_write_path_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.agent.tools import _resolve_and_validate_write_path

    monkeypatch.setattr(
        Path,
        "resolve",
        lambda self, *args, **kwargs: (_ for _ in ()).throw(OSError("access denied")),
    )
    with pytest.raises(FileNotFoundError, match="could not be resolved"):
        _resolve_and_validate_write_path("some_file.txt")


def test_allowed_write_roots_and_search_root_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    from sakthai.agent.tools import _allowed_write_roots, _resolve_search_root

    # _SHELL_ALLOW_ANY tokens skipped
    monkeypatch.setenv("SAKTHAI_WRITE_ALLOW", "any:true:*")
    roots = _allowed_write_roots()
    assert len(roots) >= 1

    # Sensitive search root raises PermissionError
    with pytest.raises(PermissionError, match="sensitive path"):
        _resolve_search_root(".git")

    # Search root outside allowed roots raises PermissionError
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))
    with pytest.raises(PermissionError, match="outside the allowed roots"):
        _resolve_search_root("/var")

    # grep_search invalid glob type
    grep_tool = tool_by_name("grep_search")
    assert grep_tool is not None
    with pytest.raises(ValueError, match="`glob` must be a string"):
        grep_tool.handler({"pattern": "foo", "path": str(tmp_path), "glob": 123}, store)
