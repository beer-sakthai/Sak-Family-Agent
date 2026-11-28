"""Tests for read-only starter tools and memory boundary enforcement."""

from __future__ import annotations

import pytest
from sak_mcp_gateway.tools import TOOL_DEFINITIONS, execute_tool


def test_tool_definitions_structure() -> None:
    names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "sak_health_status" in names
    assert "sak_family_catalog" in names
    for tool in TOOL_DEFINITIONS:
        assert "description" in tool
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"


def test_execute_sak_health_status() -> None:
    res = execute_tool("sak_health_status", {"verbose": False})
    assert res["ok"] is True
    assert res["status"] == "healthy"
    assert "active_personas" in res
    assert len(res["active_personas"]) == 6
    assert "ENFORCED" in res["memory_boundary"]
    assert "telemetry" not in res

    verbose_res = execute_tool("sak_health_status", {"verbose": True})
    assert "telemetry" in verbose_res
    assert verbose_res["telemetry"]["m365_plugin_schema"] == "v2.4"


def test_execute_sak_family_catalog_all() -> None:
    res = execute_tool("sak_family_catalog")
    assert res["ok"] is True
    personas = res["personas"]
    assert "sakthai" in personas
    assert "sakking" in personas
    assert "saksee" in personas
    assert "saksit" in personas
    assert "saktan" in personas
    assert "sakjules" in personas
    assert personas["sakthai"]["skills_count"] == 174


def test_execute_sak_family_catalog_single() -> None:
    res = execute_tool("sak_family_catalog", {"persona": "sakjules"})
    assert res["ok"] is True
    assert "sakjules" in res["personas"]
    assert res["personas"]["sakjules"]["display_name"] == "SakJules"

    unknown_res = execute_tool("sak_family_catalog", {"persona": "unknown_bot"})
    assert unknown_res["ok"] is False
    assert "Unknown persona" in unknown_res["error"]


def test_execute_unknown_tool_raises_value_error() -> None:
    with pytest.raises(ValueError, match="is not recognized"):
        execute_tool("destructive_memory_delete")
