"""Tests for tool description overrides and ingest_document input validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sakthai.agent import tools as tools_mod
from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.memory.store import MemoryStore


def _tool(name: str) -> Any:
    return next(t for t in BUILTIN_TOOLS if t.name == name)


@pytest.fixture
def restore_learn_tool() -> Any:
    """Snapshot the learn tool's mutable metadata and restore it after the test."""
    tool = _tool("learn")
    original_description = tool.description
    original_schema = tool.input_schema
    yield tool
    object.__setattr__(tool, "description", original_description)
    object.__setattr__(tool, "input_schema", original_schema)


def test_tool_overrides_apply_description_and_schema(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore_learn_tool: Any
) -> None:
    overrides_file = tmp_path / "tool_descriptions.json"
    new_schema = {"type": "object", "properties": {"text": {"type": "string"}}}
    overrides_file.write_text(
        json.dumps({"learn": {"description": "overridden", "input_schema": new_schema}}),
        encoding="utf-8",
    )
    import sakthai.config as config_mod

    monkeypatch.setattr(config_mod, "tool_descriptions_path", lambda: overrides_file)
    tools_mod._load_tool_overrides()
    assert restore_learn_tool.description == "overridden"
    assert restore_learn_tool.input_schema == new_schema


def test_tool_overrides_malformed_json_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore_learn_tool: Any
) -> None:
    overrides_file = tmp_path / "tool_descriptions.json"
    overrides_file.write_text("{not json", encoding="utf-8")
    import sakthai.config as config_mod

    monkeypatch.setattr(config_mod, "tool_descriptions_path", lambda: overrides_file)
    tools_mod._load_tool_overrides()  # must not raise
    assert restore_learn_tool.description != "overridden"


def test_tool_overrides_missing_file_is_a_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, restore_learn_tool: Any
) -> None:
    import sakthai.config as config_mod

    monkeypatch.setattr(
        config_mod, "tool_descriptions_path", lambda: tmp_path / "does-not-exist.json"
    )
    tools_mod._load_tool_overrides()  # must not raise
    assert restore_learn_tool.description != "overridden"


# ---------------------------------------------------------------------------
# ingest_document input validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("args", [{}, {"path": ""}, {"path": "   "}, {"path": 42}])
def test_ingest_document_rejects_missing_or_blank_path(
    args: dict[str, Any], store: MemoryStore
) -> None:
    with pytest.raises(ValueError, match="`path` is required"):
        _tool("ingest_document").handler(args, store)


def test_ingest_document_with_no_extractable_facts(
    tmp_path: Path, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    doc = tmp_path / "empty.md"
    doc.write_text("# Only a heading\n\n", encoding="utf-8")
    monkeypatch.setenv("SAKTHAI_READ_ALLOW", str(tmp_path))
    result = _tool("ingest_document").handler({"path": str(doc)}, store)
    assert result == "No facts found in document."
