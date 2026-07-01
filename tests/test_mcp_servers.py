"""Tests for MCP server manifest parsing and config discovery (mcp/servers.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.mcp.servers import (
    load_server_specs,
    mcp_config_path,
    parse_mcp_servers,
)


def test_mcp_config_path_honours_home(sakthai_home: Path) -> None:
    assert mcp_config_path() == sakthai_home / "mcp.json"


def test_parse_valid_manifest() -> None:
    data = {
        "mcpServers": {
            "github": {"command": "node", "args": ["s.js"], "env": {"TOKEN": "x"}},
        }
    }
    specs = parse_mcp_servers(data)
    assert "github" in specs
    assert specs["github"].command == "node"
    assert specs["github"].args == ["s.js"]
    assert specs["github"].env["TOKEN"] == "x"


def test_load_specs_merges_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    conf = tmp_path / "mcp.json"
    conf.write_text(
        json.dumps({"mcpServers": {"extra": {"command": "python", "args": ["m.py"]}}}, indent=2),
        encoding="utf-8",
    )
    specs = load_server_specs()
    assert "extra" in specs
    assert specs["extra"].command == "python"
