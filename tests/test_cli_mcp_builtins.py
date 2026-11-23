"""`--builtins` on the three MCP inspection commands.

`sakthai mcp list|ping|tools` default to `--no-builtins`, while
`cli/agent.py:_tool_context` — the path `sakthai run` and `chat` take — passes
`include_builtins=True` unconditionally. So the inspection commands show
something *different from what the agent actually loads* unless the flag is
given. That asymmetry is deliberate but surprising, and these tests pin both
sides of it so a change to either is visible.

Hermetic: no server is started. `mcp list` only reads specs, and the `ping`
tests patch the client classes.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from sakthai.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _own_manifest(sakthai_home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty manifest, so only the built-ins can appear."""
    manifest = sakthai_home / "mcp.json"
    manifest.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    monkeypatch.setenv("SAKTHAI_MCP_CONFIG", str(manifest))
    return manifest


# --- list --------------------------------------------------------------------


def test_list_hides_builtins_by_default(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "list"])
    assert result.exit_code == 0, result.output
    assert "No external MCP servers configured." in result.output


def test_list_shows_builtins_when_asked(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "list", "--builtins"])
    assert result.exit_code == 0, result.output
    for name in ("genkit", "google_dev_knowledge", "figma", "huggingface"):
        assert name in result.output


def test_list_builtins_are_scoped_to_the_persona(runner: CliRunner) -> None:
    """SakThai's loadout is huggingface alone; figma belongs to others."""
    result = runner.invoke(main, ["mcp", "list", "--builtins", "--persona", "sakthai"])
    assert result.exit_code == 0, result.output
    assert "huggingface" in result.output
    assert "figma" not in result.output


def test_list_builtins_json_reports_the_current_transport(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "list", "--builtins", "--json"])
    assert result.exit_code == 0, result.output
    rows = {r["name"]: r for r in json.loads(result.output)}
    assert rows["huggingface"]["transport"] == "streamable-http"
    assert rows["genkit"]["transport"] == "stdio"
    # The pin is visible from the CLI, which is where a reviewer would look.
    assert "genkit@1.44.0" in rows["genkit"]["args"]


# --- tools -------------------------------------------------------------------


def test_tools_reports_nothing_without_builtins(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "tools"])
    assert result.exit_code == 0, result.output
    assert "No external MCP tools available." in result.output


# --- ping --------------------------------------------------------------------


def test_ping_reaches_builtins_when_asked(runner: CliRunner) -> None:
    client = MagicMock()
    client.ping.return_value = True
    with (
        patch("sakthai.mcp.RemoteMCPClient", return_value=client),
        patch("sakthai.mcp.StdioMCPClient", return_value=client),
    ):
        result = runner.invoke(main, ["mcp", "ping", "--builtins", "--persona", "sakthai"])
    assert result.exit_code == 0, result.output
    assert "huggingface" in result.output
    assert "PONG" in result.output


def test_ping_reports_a_dead_server_without_raising(runner: CliRunner) -> None:
    client = MagicMock()
    client.ping.return_value = False
    with (
        patch("sakthai.mcp.RemoteMCPClient", return_value=client),
        patch("sakthai.mcp.StdioMCPClient", return_value=client),
    ):
        result = runner.invoke(main, ["mcp", "ping", "--builtins", "--persona", "sakthai"])
    assert result.exit_code == 0, result.output
    assert "NO PONG" in result.output


def test_ping_reports_a_raising_server_as_error(runner: CliRunner) -> None:
    client = MagicMock()
    client.start.side_effect = RuntimeError("unreachable")
    with (
        patch("sakthai.mcp.RemoteMCPClient", return_value=client),
        patch("sakthai.mcp.StdioMCPClient", return_value=client),
    ):
        result = runner.invoke(main, ["mcp", "ping", "--builtins", "--persona", "sakthai"])
    assert result.exit_code == 0, result.output
    assert "ERROR" in result.output
    assert "unreachable" in result.output


def test_ping_without_builtins_finds_nothing(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "ping"])
    assert result.exit_code == 0, result.output
    assert "No external MCP servers configured." in result.output


def test_ping_by_name_rejects_an_unknown_server(runner: CliRunner) -> None:
    result = runner.invoke(main, ["mcp", "ping", "nope", "--builtins"])
    assert result.exit_code != 0
    assert "No configured MCP server named" in result.output
