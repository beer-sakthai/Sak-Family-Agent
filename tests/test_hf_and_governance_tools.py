"""Unit tests for first-class Hugging Face and governance tools in agent/tools.py."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

from sakthai.agent.tools import Tool, tool_by_name
from sakthai.memory.store import MemoryStore


def test_hf_inspect_repo_tool_metadata() -> None:
    tool = tool_by_name("hf_inspect_repo")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "hf_inspect_repo"
    schema = tool.schema()
    assert "repo_id" in schema["input_schema"]["properties"]
    assert "repo_type" in schema["input_schema"]["properties"]
    assert "repo_id" in schema["input_schema"]["required"]


def test_hf_inspect_repo_handler_offline_or_mocked(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("hf_inspect_repo")
    assert tool is not None

    mock_model_info = MagicMock()
    mock_model_info.id = "Nanthasit/sakthai-combined-v6"
    mock_model_info.downloads = 4200
    mock_model_info.likes = 128
    mock_model_info.tags = ["safetensors", "sakthai", "text-generation"]
    mock_model_info.pipeline_tag = "text-generation"
    mock_model_info.author = "Nanthasit"
    mock_model_info.sha = "abc123456789"
    mock_model_info.lastModified = "2026-11-20T12:00:00.000Z"

    with patch("sakthai.hf._hub") as mock_hub:
        mock_hub.return_value.model_info.return_value = mock_model_info
        out = tool.handler(
            {"repo_id": "Nanthasit/sakthai-combined-v6", "repo_type": "model"}, store
        )
        data = json.loads(out)
        assert data["status"] == "ok"
        assert data["repo_id"] == "Nanthasit/sakthai-combined-v6"
        assert data["downloads"] == 4200
        assert data["likes"] == 128
        assert data["pipeline_tag"] == "text-generation"


def test_hf_portfolio_summary_tool_metadata() -> None:
    tool = tool_by_name("hf_portfolio_summary")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "hf_portfolio_summary"
    schema = tool.schema()
    assert "owner" in schema["input_schema"]["properties"]


def test_hf_portfolio_summary_handler(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("hf_portfolio_summary")
    assert tool is not None

    out = tool.handler({"owner": "Nanthasit"}, store)
    data = json.loads(out)
    assert data["status"] == "ok"
    assert data["owner"] == "Nanthasit"
    assert "total_models" in data
    assert "total_datasets" in data
    assert "total_spaces" in data
    assert "total_downloads" in data


def test_resolve_family_conflict_tool_metadata() -> None:
    tool = tool_by_name("resolve_family_conflict")
    assert tool is not None
    assert isinstance(tool, Tool)
    assert tool.name == "resolve_family_conflict"
    schema = tool.schema()
    assert "resolution_note" in schema["input_schema"]["properties"]
    assert "resolution_note" in schema["input_schema"]["required"]


def test_resolve_family_conflict_handler(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    # Add a mock conflict fact
    store.add_fact(
        kind="alert",
        value="Rate limit deadlock between SakSee and SakKing",
        key="conflict_42",
        tags=["conflict", "sakking", "saksee"],
    )

    tool = tool_by_name("resolve_family_conflict")
    assert tool is not None

    out = tool.handler(
        {
            "resolution_note": "Assigned priority lane 1 to SakKing and scheduled SakSee browser refresh",
            "target_persona": "sakking",
        },
        store,
    )
    data = json.loads(out)
    assert data["status"] == "resolved"
    assert data["resolved_by"] == "sakthai"
    assert data["conflicts_cleared"] >= 1

    # Check memory now has conflict-resolved tag
    resolved_facts = store.search_by_tag("conflict-resolved")
    assert len(resolved_facts) >= 1
