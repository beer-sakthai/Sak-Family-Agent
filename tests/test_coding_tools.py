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
