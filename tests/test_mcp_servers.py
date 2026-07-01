"""Tests for MCP server manifest parsing and config discovery (mcp/servers.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sakthai.mcp.servers import (MCPServerSpec, load_server_specs,
                                 mcp_config_path, parse_mcp_servers)


def test_mcp_config_path_honours_home(sakthai_home: Path) -> None:
    assert mcp_config_path() == sakthai_home / "mcp.json"


def test_parse_valid_manifest() -> None:
    data = {
        "mcpServers": {
            "github": {"command": "node", "args": ["s.js"], "env": {"TOKEN": "x"}},
            "db": {"command": "python", "args": ["-m", "db_mcp"], "cwd": "/srv"},
        }
    }
    specs = {s.name: s for s in parse_mcp_servers(data)}
    assert specs["github"] == MCPServerSpec("github", "node", ["s.js"], {"TOKEN": "x"})
    assert specs["db"].args == ["-m", "db_mcp"]
    assert specs["db"].cwd == "/srv"


def test_parse_skips_entries_without_command() -> None:
    data = {"mcpServers": {"bad": {"args": ["x"]}, "ok": {"command": "run"}}}
    names = [s.name for s in parse_mcp_servers(data)]
    assert names == ["ok"]


def test_parse_coerces_args_and_env() -> None:
    data = {"mcpServers": {"s": {"command": "c", "args": [1, "two"], "env": {"A": 3}}}}
    (spec,) = parse_mcp_servers(data)
    assert spec.args == ["1", "two"]
    assert spec.env == {"A": "3"}


def test_parse_tolerates_junk() -> None:
    assert parse_mcp_servers(None) == []
    assert parse_mcp_servers({"mcpServers": "nope"}) == []
    assert parse_mcp_servers({}) == []


def test_load_specs_reads_mcp_json(sakthai_home: Path) -> None:
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"a": {"command": "run-a"}}}), encoding="utf-8"
    )
    specs = load_server_specs()
    assert [s.name for s in specs] == ["a"]
    assert specs[0].command == "run-a"


def test_load_specs_includes_extension_manifests(sakthai_home: Path) -> None:
    ext = sakthai_home / "extensions" / "my-ext"
    ext.mkdir(parents=True)
    (ext / "gemini-extension.json").write_text(
        json.dumps({"mcpServers": {"fromext": {"command": "ext-run"}}}),
        encoding="utf-8",
    )
    names = {s.name for s in load_server_specs()}
    assert "fromext" in names


def test_parse_skips_non_dict_entry_values() -> None:
    data = {"mcpServers": {"bad": "not-a-dict", "ok": {"command": "run-ok"}}}
    names = [s.name for s in parse_mcp_servers(data)]
    assert names == ["ok"]


def test_load_specs_reads_gemini_extensions_dir(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.config import gemini_extensions_dir

    gemini_base = gemini_extensions_dir()
    ext = gemini_base / "my-gemini-ext"
    ext.mkdir(parents=True, exist_ok=True)
    (ext / "gemini-extension.json").write_text(
        json.dumps({"mcpServers": {"gemini-tool": {"command": "gemini-run"}}}),
        encoding="utf-8",
    )
    names = {s.name for s in load_server_specs()}
    assert "gemini-tool" in names


def test_load_manifest_handles_invalid_json(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.config import gemini_extensions_dir

    gemini_base = gemini_extensions_dir()
    ext = gemini_base / "bad-ext"
    ext.mkdir(parents=True, exist_ok=True)
    # Corrupt JSON — _load_manifest should log a warning and return []
    (ext / "gemini-extension.json").write_text("{ not valid json }", encoding="utf-8")
    # Should not raise; corrupt manifest is skipped
    specs = load_server_specs()
    assert all(s.name != "bad-ext" for s in specs)


def test_mcp_json_overrides_extension_on_name_clash(sakthai_home: Path) -> None:
    ext = sakthai_home / "extensions" / "e"
    ext.mkdir(parents=True)
    (ext / "gemini-extension.json").write_text(
        json.dumps({"mcpServers": {"dup": {"command": "ext-cmd"}}}), encoding="utf-8"
    )
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"dup": {"command": "config-cmd"}}}), encoding="utf-8"
    )
    specs = {s.name: s for s in load_server_specs()}
    assert specs["dup"].command == "config-cmd"  # mcp.json wins


def test_persona_override_adds_servers(
    sakthai_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    persona_cfg = tmp_path / "persona-mcp.json"
    persona_cfg.write_text(
        json.dumps({"mcpServers": {"playwright": {"command": "npx"}}}), encoding="utf-8"
    )
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(persona_cfg))
    names = {s.name for s in load_server_specs()}
    assert "playwright" in names


def test_persona_override_wins_on_name_clash(
    sakthai_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (sakthai_home / "mcp.json").write_text(
        json.dumps({"mcpServers": {"dup": {"command": "shared-cmd"}}}), encoding="utf-8"
    )
    persona_cfg = tmp_path / "persona-mcp.json"
    persona_cfg.write_text(
        json.dumps({"mcpServers": {"dup": {"command": "persona-cmd"}}}),
        encoding="utf-8",
    )
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(persona_cfg))
    specs = {s.name: s for s in load_server_specs()}
    assert specs["dup"].command == "persona-cmd"  # persona override wins over shared


def test_persona_override_missing_file_is_ignored(
    sakthai_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(tmp_path / "nope.json"))
    # Should not raise; a missing override file is simply skipped.
    assert load_server_specs() == []
