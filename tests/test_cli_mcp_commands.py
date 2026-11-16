"""Tests for sakthai mcp CLI subcommands (list, ping, tools, serve)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_mcp_list_empty(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    result = runner.invoke(main, ["mcp", "list"])
    assert result.exit_code == 0
    assert "No external MCP servers configured" in result.output


def test_cli_mcp_list_with_servers(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    conf = tmp_path / "mcp.json"
    conf.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "srv1": {
                        "command": "node",
                        "args": ["s.js"],
                        "tools": ["tool_a", "tool_b"],
                    },
                    "remote_srv": {
                        "url": "https://mcp.feather.so",
                        "transport": "sse",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    # Standard table output
    result = runner.invoke(main, ["mcp", "list"])
    assert result.exit_code == 0
    assert "Configured MCP server(s) (2):" in result.output
    assert "srv1" in result.output
    assert "tool_a, tool_b" in result.output
    assert "remote_srv" in result.output
    assert "https://mcp.feather.so" in result.output

    # JSON output
    json_result = runner.invoke(main, ["mcp", "list", "--json"])
    assert json_result.exit_code == 0
    data = json.loads(json_result.output)
    assert len(data) == 2
    names = {d["name"] for d in data}
    assert names == {"srv1", "remote_srv"}


def test_cli_mcp_ping(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    conf = tmp_path / "mcp.json"
    conf.write_text(
        json.dumps({"mcpServers": {"srv1": {"command": "dummy", "args": []}}}),
        encoding="utf-8",
    )

    mock_client = MagicMock()
    mock_client.ping.return_value = True

    monkeypatch.setattr("sakthai.mcp.StdioMCPClient", lambda *args, **kwargs: mock_client)

    result = runner.invoke(main, ["mcp", "ping"])
    assert result.exit_code == 0
    assert "PONG" in result.output
    mock_client.start.assert_called_once()
    mock_client.close.assert_called_once()


def test_cli_mcp_ping_unknown_server(
    runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    result = runner.invoke(main, ["mcp", "ping", "unknown_srv"])
    assert result.exit_code != 0
    assert "No configured MCP server named 'unknown_srv'" in result.output


def test_cli_mcp_tools(runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.agent.tools import Tool

    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    conf = tmp_path / "mcp.json"
    conf.write_text(
        json.dumps({"mcpServers": {"srv1": {"command": "dummy", "args": []}}}),
        encoding="utf-8",
    )

    fake_tools = [
        Tool(
            name="srv1__do_something",
            description="Does something useful",
            input_schema={"type": "object"},
            handler=lambda args, store: "done",
        )
    ]

    import contextlib

    @contextlib.contextmanager
    def fake_connect(*args, **kwargs):
        yield fake_tools

    monkeypatch.setattr("sakthai.mcp.manager.connect_servers", fake_connect)

    result = runner.invoke(main, ["mcp", "tools"])
    assert result.exit_code == 0
    assert "Available external MCP tool(s) (1):" in result.output
    assert "srv1__do_something" in result.output


def test_cli_mcp_serve_subcommand(runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.mcp as mcp_pkg

    called = False

    def fake_serve() -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(mcp_pkg, "serve", fake_serve)
    result = runner.invoke(main, ["mcp", "serve"])
    assert result.exit_code == 0
    assert called is True
