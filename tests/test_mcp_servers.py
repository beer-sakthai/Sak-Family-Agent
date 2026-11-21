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


def test_parse_servers_list_format() -> None:
    data = {
        "servers": [
            {
                "name": "sakking",
                "command": "sakking",
                "args": ["mcp", "serve"],
                "env": {"FOO": "bar"},
            },
            {
                "name": "feather",
                "url": "https://mcp.feather.so",
                "transport": "sse",
                "tools": ["list_blogs", "create_post"],
            },
        ]
    }
    specs = parse_mcp_servers(data)
    assert len(specs) == 2
    by_name = {s.name: s for s in specs}
    assert by_name["sakking"].command == "sakking"
    assert by_name["sakking"].args == ["mcp", "serve"]
    assert by_name["sakking"].env == {"FOO": "bar"}
    assert by_name["sakking"].transport == "stdio"

    assert by_name["feather"].url == "https://mcp.feather.so"
    assert by_name["feather"].transport == "sse"
    assert by_name["feather"].tools == ["list_blogs", "create_post"]


def test_parse_servers_dict_format() -> None:
    data = {
        "servers": {
            "remote_srv": {
                "url": "https://example.com/mcp",
                "tools": ["tool_a"],
            }
        }
    }
    specs = parse_mcp_servers(data)
    assert len(specs) == 1
    assert specs[0].name == "remote_srv"
    assert specs[0].url == "https://example.com/mcp"
    assert specs[0].transport == "sse"
    assert specs[0].tools == ["tool_a"]


def test_parse_local_type_maps_to_stdio() -> None:
    data = {
        "mcpServers": {
            "gh_aw": {
                "type": "local",
                "command": "gh",
                "args": ["aw", "mcp-server"],
                "tools": ["compile", "audit"],
            }
        }
    }
    specs = parse_mcp_servers(data)
    assert len(specs) == 1
    assert specs[0].transport == "stdio"
    assert specs[0].tools == ["compile", "audit"]


def test_parse_headers_with_env_expansion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STEP_SECURITY_API_KEY", "step_mock_token_12345")
    data = {
        "mcpServers": {
            "stepsecurity": {
                "url": "https://agent.api.stepsecurity.io/v1/mcp?customer=beer-sakthai",
                "headers": {
                    "Authorization": "Bearer ${STEP_SECURITY_API_KEY}",
                    "X-Custom-Header": "constant-value",
                },
            }
        }
    }
    specs = parse_mcp_servers(data)
    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "stepsecurity"
    assert spec.url == "https://agent.api.stepsecurity.io/v1/mcp?customer=beer-sakthai"
    assert spec.transport == "sse"
    assert spec.headers["Authorization"] == "Bearer step_mock_token_12345"
    assert spec.headers["X-Custom-Header"] == "constant-value"


def test_parse_sandbox_flag() -> None:
    data = {
        "mcpServers": {
            "sandboxed_srv": {
                "command": "python",
                "args": ["-m", "isolated_server"],
                "sandbox": True,
            }
        }
    }
    specs = parse_mcp_servers(data)
    assert len(specs) == 1
    assert specs[0].sandbox is True


def test_parse_mcp_servers_additional_branches() -> None:
    # 1. Custom transport
    specs = parse_mcp_servers({"mcpServers": {"ws": {"command": "node", "type": "websocket"}}})
    assert len(specs) == 1
    assert specs[0].transport == "websocket"

    # 2. servers list with non-dict and missing name
    specs_list = parse_mcp_servers({"servers": ["junk", {"no_name": True}, {"name": "valid", "command": "python"}]})
    assert len(specs_list) == 1
    assert specs_list[0].name == "valid"

    # 3. servers dict with non-dict entry
    specs_dict = parse_mcp_servers({"servers": {"bad": "not_dict", "good": {"command": "python"}}})
    assert len(specs_dict) == 1
    assert specs_dict[0].name == "good"

    # 4. _parse_server_entry directly with non-dict
    from sakthai.mcp.servers import _parse_server_entry
    assert _parse_server_entry("bad", "not_dict") is None


