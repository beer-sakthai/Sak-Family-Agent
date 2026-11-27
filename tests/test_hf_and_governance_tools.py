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


def test_hf_inspect_repo_edge_cases(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("hf_inspect_repo")
    assert tool is not None

    # Missing repo_id
    out = tool.handler({"repo_id": ""}, store)
    assert json.loads(out)["status"] == "error"

    # Dataset repo
    mock_ds_info = MagicMock()
    mock_ds_info.id = "Nanthasit/eval-set"
    mock_ds_info.downloads = 100
    mock_ds_info.likes = 10
    mock_ds_info.tags = ["dataset"]
    mock_ds_info.pipeline_tag = None
    mock_ds_info.author = "Nanthasit"
    mock_ds_info.sha = "123"
    mock_ds_info.lastModified = "2026-11-20"

    with patch("sakthai.hf._hub") as mock_hub:
        mock_hub.return_value.dataset_info.return_value = mock_ds_info
        out = tool.handler({"repo_id": "Nanthasit/eval-set", "repo_type": "dataset"}, store)
        assert json.loads(out)["status"] == "ok"
        assert json.loads(out)["repo_type"] == "dataset"

    # Space repo
    mock_space_info = MagicMock()
    mock_space_info.id = "Nanthasit/demo-space"
    mock_space_info.downloads = 50
    mock_space_info.likes = 5
    mock_space_info.tags = []
    mock_space_info.pipeline_tag = None
    mock_space_info.author = "Nanthasit"
    mock_space_info.sha = "456"
    mock_space_info.lastModified = "2026-11-20"

    with patch("sakthai.hf._hub") as mock_hub:
        mock_hub.return_value.space_info.return_value = mock_space_info
        out = tool.handler({"repo_id": "Nanthasit/demo-space", "repo_type": "space"}, store)
        assert json.loads(out)["status"] == "ok"
        assert json.loads(out)["repo_type"] == "space"

    # Exception during inspect
    with patch("sakthai.hf._hub", side_effect=RuntimeError("connection error")):
        out = tool.handler({"repo_id": "Nanthasit/broken"}, store)
        assert json.loads(out)["status"] == "error"
        assert "connection error" in json.loads(out)["error"]


def test_hf_portfolio_summary_cached(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("hf_portfolio_summary")
    assert tool is not None

    # First call primes cache
    out1 = tool.handler({"owner": "Nanthasit"}, store)
    assert json.loads(out1)["status"] == "ok"

    # Second call uses cache
    out2 = tool.handler({"owner": "Nanthasit"}, store)
    assert out1 == out2

    # Force refresh bypasses cache
    out3 = tool.handler({"owner": "Nanthasit", "force_refresh": True}, store)
    assert json.loads(out3)["status"] == "ok"


def test_resolve_family_conflict_missing_note_and_all_targets(tmp_path: Any) -> None:
    store = MemoryStore(tmp_path / "memory.db")
    tool = tool_by_name("resolve_family_conflict")
    assert tool is not None

    # Missing note
    out = tool.handler({"resolution_note": ""}, store)
    assert json.loads(out)["status"] == "error"

    # Resolving for all without specific target_persona
    store.add_fact(
        kind="alert",
        value="General dispute",
        key="dispute_1",
        tags=["conflict"],
    )
    out = tool.handler({"resolution_note": "Rebalanced workloads"}, store)
    data = json.loads(out)
    assert data["status"] == "resolved"
    assert data["target_persona"] == "all"
    assert data["conflicts_cleared"] >= 1


def test_triple_gate_safety_contract(tmp_path: Any) -> None:
    from sakthai.hf import (
        TripleGateError,
        assert_hf_write_allowed,
        triple_gate_hub_write,
    )

    store = MemoryStore(tmp_path / "memory.db")

    # Gate 1: Insufficient charge
    import pytest

    with pytest.raises(TripleGateError, match="Gate 1 violation"):
        assert_hf_write_allowed(store=store, current_charge=30.0)

    with pytest.raises(TripleGateError, match="Gate 1 violation"):
        assert_hf_write_allowed(store=store, current_charge="40%")

    with pytest.raises(TripleGateError, match="Gate 1 violation"):
        assert_hf_write_allowed(store=store, current_charge="low")

    # No store provided -> Gate 2 & 3 violation
    with pytest.raises(TripleGateError, match="Gate 2 & 3 violation"):
        assert_hf_write_allowed(store=None, current_charge=60.0)

    # Gate 3: Missing hub-approved tag
    with pytest.raises(TripleGateError, match="Gate 3 violation"):
        assert_hf_write_allowed(store=store, current_charge="active")

    # Gate 2: Active deputy-chain tag
    store.add_fact(kind="alert", value="emergency routing", key="em_1", tags=["deputy-chain"])
    with pytest.raises(TripleGateError, match="Gate 2 violation"):
        assert_hf_write_allowed(store=store, current_charge="active")

    # Clear deputy-chain and add hub-approved tag
    store.update_fact(1, "resolved emergency", tags=["resolved"])
    store.add_fact(kind="approval", value="approved", key="app_1", tags=["hub-approved"])
    assert assert_hf_write_allowed(store=store, current_charge="active") is True

    # Test decorator
    @triple_gate_hub_write
    def dummy_write(repo_id: str, store: Any = None, current_charge: Any = "active") -> str:
        return f"written {repo_id}"

    res = dummy_write("test/model", store=store)
    assert res == "written test/model"

    # Test decorator with positional store argument
    @triple_gate_hub_write
    def dummy_write_pos(store_arg: Any, repo_id: str) -> str:
        return f"pos {repo_id}"

    assert dummy_write_pos(store, "test/model") == "pos test/model"

    # Direct branch tests on _is_charge_sufficient
    from sakthai.hf import _is_charge_sufficient

    assert _is_charge_sufficient(None) is True
    assert _is_charge_sufficient(60.0) is True
    assert _is_charge_sufficient(30.0) is False
    assert _is_charge_sufficient("30%") is False
    assert _is_charge_sufficient("80%") is True
    assert _is_charge_sufficient("chargelevel.active") is True
    assert _is_charge_sufficient("chargelevel.critical") is True
    assert _is_charge_sufficient("chargelevel.low") is False
    assert _is_charge_sufficient("chargelevel.none") is False


def test_hf_validate_card_metadata_valid(tmp_path: Any) -> None:
    from sakthai.hf import hf_validate_card_metadata

    valid_content = """---
language:
- en
- th
license: apache-2.0
tags:
- text-generation
- sakthai
pipeline_tag: text-generation
---

# SakThai Combined Model
This is an awesome local-first open-weight model.
"""
    # Test from string content
    res = hf_validate_card_metadata(valid_content)
    assert res["valid"] is True
    assert res["errors"] == []
    assert res["metadata"]["license"] == "apache-2.0"
    assert res["metadata"]["language"] == ["en", "th"]

    # Test from file path
    card_file = tmp_path / "README.md"
    card_file.write_text(valid_content, encoding="utf-8")
    file_res = hf_validate_card_metadata(card_file)
    assert file_res["valid"] is True
    assert file_res["metadata"]["license"] == "apache-2.0"


def test_hf_validate_card_metadata_errors_and_warnings(tmp_path: Any) -> None:
    from sakthai.hf import hf_validate_card_metadata

    # Missing frontmatter
    no_fm = "# Just a markdown file without YAML frontmatter"
    res1 = hf_validate_card_metadata(no_fm)
    assert res1["valid"] is False
    assert any("Missing YAML frontmatter" in e for e in res1["errors"])

    # Invalid YAML syntax
    bad_yaml = "---\nlicense: [unclosed list\n---\n"
    res2 = hf_validate_card_metadata(bad_yaml)
    assert res2["valid"] is False
    assert any("YAML parsing error" in e for e in res2["errors"])

    # Non-dictionary YAML (e.g. list)
    list_yaml = "---\n- item1\n- item2\n---\n"
    res3 = hf_validate_card_metadata(list_yaml)
    assert res3["valid"] is False
    assert any("must parse to a dictionary" in e for e in res3["errors"])

    # Missing license
    no_license = "---\nlanguage: en\ntags:\n- nlp\n---\n"
    res4 = hf_validate_card_metadata(no_license)
    assert res4["valid"] is False
    assert any("Missing required metadata field: 'license'" in e for e in res4["errors"])

    # Warnings: missing pipeline_tag/tags, invalid language type
    warn_content = "---\nlicense: mit\nlanguage: 12345\n---\n"
    res5 = hf_validate_card_metadata(warn_content)
    assert res5["valid"] is True
    assert any("Recommended metadata missing" in w for w in res5["warnings"])
    assert any("'language' field should be str or list of str" in w for w in res5["warnings"])
