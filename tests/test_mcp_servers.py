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
    assert any(s.name == "github" for s in specs)
    spec = next(s for s in specs if s.name == "github")
    assert spec.command == "node"
    assert spec.args == ["s.js"]
    assert spec.env["TOKEN"] == "x"


def test_load_specs_merges_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    conf = tmp_path / "mcp.json"
    conf.write_text(
        json.dumps({"mcpServers": {"extra": {"command": "python", "args": ["m.py"]}}}, indent=2),
        encoding="utf-8",
    )
    specs = load_server_specs()
    assert any(s.name == "extra" for s in specs)
    spec = next(s for s in specs if s.name == "extra")
    assert spec.command == "python"


# -- parse_mcp_servers: tolerance of junk --------------------------------


@pytest.mark.parametrize(
    "data",
    [
        "not a dict",
        123,
        None,
        [],
        {},  # no "mcpServers" key
        {"mcpServers": "not a dict"},
        {"mcpServers": []},
    ],
)
def test_parse_returns_empty_for_junk_top_level(data: object) -> None:
    assert parse_mcp_servers(data) == []


@pytest.mark.parametrize(
    "entry",
    [
        "not a dict",
        123,
        None,
        [],
        {},  # missing "command"
        {"command": ""},  # empty command
        {"command": 42},  # non-string command
        {"args": ["x"]},  # command absent
    ],
)
def test_parse_skips_invalid_entries(entry: object) -> None:
    assert parse_mcp_servers({"mcpServers": {"srv": entry}}) == []


def test_parse_keeps_valid_entries_and_drops_invalid_siblings() -> None:
    data = {
        "mcpServers": {
            "good": {"command": "node", "args": ["s.js"]},
            "bad": {"command": ""},
        }
    }
    specs = parse_mcp_servers(data)
    assert [s.name for s in specs] == ["good"]


def test_parse_coerces_args_and_env_and_defaults() -> None:
    data = {
        "mcpServers": {
            "srv": {
                "command": "node",
                "args": [1, "two", 3.0],
                "env": {"A": 1, "B": "two"},
                "cwd": "/work",
            },
            "sparse": {"command": "py", "args": "not-a-list", "env": "nope"},
        }
    }
    specs = {s.name: s for s in parse_mcp_servers(data)}
    assert specs["srv"].args == ["1", "two", "3.0"]
    assert specs["srv"].env == {"A": "1", "B": "two"}
    assert specs["srv"].cwd == "/work"
    # Non-list args / non-dict env fall back to empty; absent cwd is None.
    assert specs["sparse"].args == []
    assert specs["sparse"].env == {}
    assert specs["sparse"].cwd is None


# -- _load_manifest: read/parse error handling ---------------------------


def test_load_manifest_skips_unreadable_file(tmp_path: Path) -> None:
    from sakthai.mcp.servers import _load_manifest

    assert _load_manifest(tmp_path / "does-not-exist.json") == []


def test_load_manifest_skips_malformed_json(tmp_path: Path) -> None:
    from sakthai.mcp.servers import _load_manifest

    bad = tmp_path / "mcp.json"
    bad.write_text("{not valid json", encoding="utf-8")
    assert _load_manifest(bad) == []


# -- load_server_specs: layered precedence -------------------------------


def _write_manifest(path: Path, name: str, command: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"mcpServers": {name: {"command": command}}}),
        encoding="utf-8",
    )


def test_load_specs_gathers_all_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "sakthai"
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    monkeypatch.delenv("GEMINI_HOME", raising=False)

    # gemini extension (home.parent / "gemini" / "extensions" / <ext> / manifest)
    _write_manifest(
        tmp_path / "gemini" / "extensions" / "g" / "gemini-extension.json",
        "gemini-srv",
        "gcmd",
    )
    # sakthai extension (home / "extensions" / <ext> / manifest)
    _write_manifest(home / "extensions" / "s" / "gemini-extension.json", "sakthai-srv", "scmd")
    # shared primary config (home / "mcp.json")
    _write_manifest(home / "mcp.json", "shared-srv", "ccmd")
    # persona override
    override = tmp_path / "persona.json"
    _write_manifest(override, "persona-srv", "pcmd")
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(override))

    by_name = {s.name: s for s in load_server_specs()}
    assert set(by_name) == {"gemini-srv", "sakthai-srv", "shared-srv", "persona-srv"}
    assert by_name["gemini-srv"].command == "gcmd"
    assert by_name["persona-srv"].command == "pcmd"


@pytest.mark.parametrize(
    ("winning_source", "expected_command"),
    [
        ("gemini", "gcmd"),
        ("sakthai", "scmd"),
        ("shared", "ccmd"),
        ("persona", "pcmd"),
    ],
)
def test_load_specs_precedence_last_source_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    winning_source: str,
    expected_command: str,
) -> None:
    """Same server name at every layer: higher-precedence sources override lower.

    Precedence, lowest → highest: gemini ext → sakthai ext → mcp.json → persona.
    We seed the name "dup" up to the tier under test and assert the winner.
    """
    home = tmp_path / "sakthai"
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    monkeypatch.delenv("GEMINI_HOME", raising=False)
    monkeypatch.delenv("SAKTHAI_MCP_CONFIG", raising=False)

    tiers = ["gemini", "sakthai", "shared", "persona"]
    include = tiers[: tiers.index(winning_source) + 1]

    if "gemini" in include:
        _write_manifest(
            tmp_path / "gemini" / "extensions" / "g" / "gemini-extension.json",
            "dup",
            "gcmd",
        )
    if "sakthai" in include:
        _write_manifest(home / "extensions" / "s" / "gemini-extension.json", "dup", "scmd")
    if "shared" in include:
        _write_manifest(home / "mcp.json", "dup", "ccmd")
    if "persona" in include:
        override = tmp_path / "persona.json"
        _write_manifest(override, "dup", "pcmd")
        monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(override))

    by_name = {s.name: s for s in load_server_specs()}
    assert by_name["dup"].command == expected_command


def test_load_specs_ignores_missing_persona_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "sakthai"
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(tmp_path / "nope.json"))
    _write_manifest(home / "mcp.json", "shared-srv", "ccmd")
    by_name = {s.name: s for s in load_server_specs()}
    assert set(by_name) == {"shared-srv"}
