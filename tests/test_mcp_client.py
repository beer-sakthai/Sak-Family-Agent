"""End-to-end tests for the MCP client.

These launch the project's own MCP server (`python -m sakthai.mcp`) as the
"external" server in a subprocess pointed at an isolated SAKTHAI_HOME, then drive
it through StdioMCPClient. No network; the only process spawned is this same
Python interpreter running the server.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sakthai.mcp.client import MCPClientError, MCPToolError, StdioMCPClient
from sakthai.memory.store import MemoryStore


def _server(home: Path) -> StdioMCPClient:
    home.mkdir(exist_ok=True)
    return StdioMCPClient(
        sys.executable,
        ["-m", "sakthai.mcp"],
        env={"SAKTHAI_HOME": str(home)},
        name="sakthai",
    )


def test_lists_and_calls_remote_tool(tmp_path: Path) -> None:
    home = tmp_path / "home"
    with _server(home) as client:
        names = [t["name"] for t in client.list_tools()]
        assert "learn" in names
        assert "recall" in names
        out = client.call_tool("learn", {"value": "written via mcp client"})
        assert isinstance(out, str) and out
    # The server wrote to its own DB; confirm the round-trip persisted.
    with MemoryStore(home / "memory.db") as store:
        assert any("written via mcp client" in f.value for f in store.list_facts())


def test_as_tools_handler_dispatches_remotely(tmp_path: Path) -> None:
    home = tmp_path / "home"
    with _server(home) as client:
        tools = client.as_tools()
        assert "learn" in {t.name for t in tools}
        learn = next(t for t in tools if t.name == "learn")
        # store arg is ignored by remote tools; pass a throwaway store
        with MemoryStore(tmp_path / "local.db") as local:
            result = learn.handler({"value": "through the handler"}, local)
        assert isinstance(result, str)
    with MemoryStore(home / "memory.db") as store:
        assert any("through the handler" in f.value for f in store.list_facts())


def test_as_tools_prefix_namespaces(tmp_path: Path) -> None:
    home = tmp_path / "home"
    with _server(home) as client:
        names = {t.name for t in client.as_tools(prefix="sk_")}
    assert "sk_learn" in names
    assert "sk_recall" in names


def test_unknown_tool_raises(tmp_path: Path) -> None:
    home = tmp_path / "home"
    with _server(home) as client, pytest.raises(MCPToolError):
        client.call_tool("does_not_exist", {})


def test_start_failure_on_bad_command() -> None:
    client = StdioMCPClient("sakthai-no-such-binary-zzz", name="bad")
    with pytest.raises(MCPClientError):
        client.start()


def test_server_that_exits_immediately_fails_loudly() -> None:
    client = StdioMCPClient(sys.executable, ["-c", "pass"], name="dead", timeout=10.0)
    with pytest.raises(MCPClientError):
        client.start()
    client.close()


# -- unit tests for internal helpers (no subprocess) ---------------------


def test_extract_text_basic() -> None:
    from sakthai.mcp.client import _extract_text

    assert _extract_text([{"type": "text", "text": "hello"}]) == "hello"


def test_extract_text_joins_multiple_blocks() -> None:
    from sakthai.mcp.client import _extract_text

    assert _extract_text([{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]) == "a\nb"


def test_extract_text_empty_list() -> None:
    from sakthai.mcp.client import _extract_text

    assert _extract_text([]) == ""


def test_extract_text_non_list_returns_empty() -> None:
    from sakthai.mcp.client import _extract_text

    assert _extract_text("not a list") == ""
    assert _extract_text(None) == ""


def test_extract_text_skips_non_text_blocks() -> None:
    from sakthai.mcp.client import _extract_text

    content = [{"type": "image", "url": "x"}, {"type": "text", "text": "hi"}]
    assert _extract_text(content) == "hi"


def test_call_tool_raises_on_is_error() -> None:
    client = StdioMCPClient("dummy", name="test")

    def fake_request(method: str, params: dict | None = None) -> dict:
        return {"result": {"isError": True, "content": [{"type": "text", "text": "tool bombed"}]}}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(MCPToolError, match="tool bombed"):
        client.call_tool("failing_tool")


def test_call_tool_raises_on_rpc_level_error() -> None:
    client = StdioMCPClient("dummy", name="test")

    def fake_request(method: str, params: dict | None = None) -> dict:
        return {"error": {"message": "method not found"}}

    client._request = fake_request  # type: ignore[method-assign]
    with pytest.raises(MCPToolError, match="method not found"):
        client.call_tool("any_tool")


def test_as_tools_skips_descriptor_without_name() -> None:
    client = StdioMCPClient("dummy", name="test")
    client._remote_tools = [
        {"description": "no name key here", "inputSchema": {}},
        {
            "name": "valid_tool",
            "description": "has a name",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]
    tools = client.as_tools()
    assert len(tools) == 1
    assert tools[0].name == "valid_tool"


def test_as_tools_defaults_missing_schema() -> None:
    client = StdioMCPClient("dummy", name="test")
    client._remote_tools = [{"name": "no_schema_tool", "description": "no schema"}]
    tools = client.as_tools()
    assert len(tools) == 1
    assert tools[0].input_schema == {"type": "object", "properties": {}}
