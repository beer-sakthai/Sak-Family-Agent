"""Tests for connect_servers and an agent run that calls an external MCP tool.

These spawn the project's own MCP server (`python -m sakthai.mcp`) as the
external server and drive the agent loop with a fake LLM client, proving the
whole plugin path: discover -> connect -> namespaced tools -> registry dispatch
-> remote subprocess. No network.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.loop import run_agent
from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.mcp.client import MCPClientError
from sakthai.mcp.manager import connect_servers
from sakthai.mcp.servers import MCPServerSpec
from sakthai.memory.store import MemoryStore


def _spec(home: Path) -> MCPServerSpec:
    home.mkdir(parents=True, exist_ok=True)
    return MCPServerSpec(
        name="sk",
        command=sys.executable,
        args=["-m", "sakthai.mcp"],
        env={"SAKTHAI_HOME": str(home)},
    )


# -- a minimal fake LLM client (one canned response per .create call) ----


class _Block:
    def __init__(self, **kwargs: Any) -> None:
        self.type = ""
        self.text = ""
        self.id = ""
        self.name = ""
        self.input: dict = {}
        self.__dict__.update(kwargs)


class _Resp:
    def __init__(self, stop_reason: str, content: list) -> None:
        self.stop_reason = stop_reason
        self.content = content


class _Messages:
    def __init__(self, responses: list) -> None:
        self._responses = responses
        self.calls = 0

    def create(self, **_kwargs: Any) -> _Resp:
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


class _FakeClient:
    def __init__(self, responses: list) -> None:
        self.messages = _Messages(responses)


def test_connect_servers_namespaces_tools(tmp_path: Path) -> None:
    with connect_servers([_spec(tmp_path / "h")], timeout=15.0) as tools:
        names = {t.name for t in tools}
    assert "sk__learn" in names
    assert "sk__recall" in names


def test_bad_server_is_skipped_others_survive(tmp_path: Path) -> None:
    bad = MCPServerSpec(name="bad", command="sakthai-no-such-binary-zzz")
    with connect_servers([bad, _spec(tmp_path / "h")], timeout=15.0) as tools:
        names = {t.name for t in tools}
    assert any(n.startswith("sk__") for n in names)
    assert not any(n.startswith("bad__") for n in names)


def test_no_specs_is_noop(tmp_path: Path) -> None:
    with connect_servers([]) as tools:
        assert tools == []


def test_agent_run_dispatches_to_external_mcp_tool(tmp_path: Path) -> None:
    server_home = tmp_path / "server"
    client = _FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="sk__learn", input={"value": "via plugin"})],
            ),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    with (
        connect_servers([_spec(server_home)], timeout=15.0) as mcp_tools,
        MemoryStore(tmp_path / "local.db") as local,
    ):
        result = run_agent(
            "remember it",
            client=client,
            store=local,
            provider="anthropic",
            tools=(*BUILTIN_TOOLS, *mcp_tools),
        )
    assert result.stop_reason == "end_turn"
    assert any(c["name"] == "sk__learn" and not c["is_error"] for c in result.tool_calls)
    # The fact was written to the EXTERNAL server's DB, not the agent's store.
    with MemoryStore(server_home / "memory.db") as srv:
        assert any("via plugin" in f.value for f in srv.list_facts())
    with MemoryStore(tmp_path / "local.db") as local:
        assert not any("via plugin" in f.value for f in local.list_facts())


# ---------------------------------------------------------------------------
# Mock-based unit tests (no real subprocess)
# ---------------------------------------------------------------------------


class TestConnectServersMocked:
    """Unit tests using mocks so no subprocesses are spawned."""

    def test_specs_none_calls_load_server_specs(self) -> None:
        with (
            patch("sakthai.mcp.manager.load_server_specs", return_value=[]) as mock_load,
            connect_servers() as tools,
        ):
            pass
        mock_load.assert_called_once()
        assert tools == []

    def test_all_servers_fail_yields_empty_list(self) -> None:
        spec = MCPServerSpec(name="broken", command="no-such-binary")
        mock_client = MagicMock()
        mock_client.start.side_effect = MCPClientError("start failed")
        with (
            patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client),
            connect_servers([spec]) as tools,
        ):
            assert tools == []
        mock_client.close.assert_called()

    def test_close_called_even_when_body_raises(self) -> None:
        spec = MCPServerSpec(name="srv", command="cmd")
        mock_client = MagicMock()
        mock_client.as_tools.return_value = []
        with (
            pytest.raises(RuntimeError, match="body error"),
            patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client),
            connect_servers([spec]),
        ):
            raise RuntimeError("body error")
        mock_client.close.assert_called()

    def test_timeout_forwarded_to_stdio_client(self) -> None:
        spec = MCPServerSpec(name="srv", command="cmd")
        mock_client = MagicMock()
        mock_client.as_tools.return_value = []
        with (
            patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client) as MockClient,
            connect_servers([spec], timeout=42.5),
        ):
            pass
        _, kwargs = MockClient.call_args
        assert kwargs.get("timeout") == 42.5

    def test_as_tools_called_with_name_prefix(self) -> None:
        spec = MCPServerSpec(name="myserver", command="cmd")
        mock_client = MagicMock()
        mock_client.as_tools.return_value = []
        with (
            patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client),
            connect_servers([spec]),
        ):
            pass
        mock_client.as_tools.assert_called_once_with(prefix="myserver__")

    def test_failed_server_does_not_block_next_server(self) -> None:
        bad_spec = MCPServerSpec(name="bad", command="no-such-binary")
        good_spec = MCPServerSpec(name="good", command="cmd")
        bad_client = MagicMock()
        bad_client.start.side_effect = MCPClientError("boom")
        good_client = MagicMock()
        fake_tool = MagicMock()
        fake_tool.name = "good__do_thing"
        good_client.as_tools.return_value = [fake_tool]

        def _make_client(command: str, *args: Any, **kwargs: Any) -> MagicMock:
            return bad_client if command == "no-such-binary" else good_client

        with (
            patch("sakthai.mcp.manager.StdioMCPClient", side_effect=_make_client),
            connect_servers([bad_spec, good_spec]) as tools,
        ):
            assert len(tools) == 1
            assert tools[0].name == "good__do_thing"

    def test_no_specs_yields_empty_without_touching_clients(self) -> None:
        with (
            patch("sakthai.mcp.manager.StdioMCPClient") as MockClient,
            connect_servers([]) as tools,
        ):
            assert tools == []
        MockClient.assert_not_called()
