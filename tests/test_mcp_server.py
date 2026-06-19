"""Tests for the MCP JSON-RPC request handler and stdio loop."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from sakthai.agent.tools import Tool
from sakthai.mcp.server import PROTOCOL_VERSION, handle_request, serve
from sakthai.memory.store import MemoryStore

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _raising_tool(name: str, exc: Exception) -> Tool:
    """Build a Tool whose handler always raises ``exc``."""

    def _handler(args: dict, store: MemoryStore) -> str:
        raise exc

    return Tool(
        name=name,
        description="a tool that always raises",
        input_schema={"type": "object", "properties": {}},
        handler=_handler,
    )


def test_initialize_echoes_protocol(store: MemoryStore) -> None:
    resp = handle_request(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "x"}},
        store,
    )
    assert resp["result"]["protocolVersion"] == "x"
    assert resp["result"]["serverInfo"]["name"] == "sakthai"


def test_initialize_default_protocol(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize"}, store)
    assert resp["result"]["protocolVersion"] == PROTOCOL_VERSION


def test_tools_list(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, store)
    names = {t["name"] for t in resp["result"]["tools"]}
    assert {"learn", "recall", "search", "forget"} <= names
    assert "inputSchema" in resp["result"]["tools"][0]


def test_tools_call_learn(store: MemoryStore) -> None:
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "hi"}},
        },
        store,
    )
    assert resp["result"]["isError"] is False
    assert "Stored fact" in resp["result"]["content"][0]["text"]


def test_tools_call_unknown_tool(store: MemoryStore) -> None:
    resp = handle_request(
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope"}},
        store,
    )
    assert resp["result"]["isError"] is True


def test_invalid_jsonrpc(store: MemoryStore) -> None:
    resp = handle_request({"method": "x"}, store)
    assert resp["error"]["code"] == -32600


def test_unknown_method(store: MemoryStore) -> None:
    resp = handle_request({"jsonrpc": "2.0", "id": 9, "method": "bogus"}, store)
    assert resp["error"]["code"] == -32601


def test_notification_returns_none(store: MemoryStore) -> None:
    assert handle_request({"jsonrpc": "2.0", "method": "notifications/x"}, store) is None
    assert handle_request({"jsonrpc": "2.0", "method": "ping"}, store) is None


def test_serve_loop(store: MemoryStore) -> None:
    stdin = io.StringIO(
        '{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n'
        "not json\n"
        '{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
    )
    stdout = io.StringIO()
    serve(store=store, stdin=stdin, stdout=stdout)
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert lines[0]["id"] == 1
    assert lines[1]["error"]["code"] == -32700  # parse error for "not json"
    assert lines[2]["id"] == 2


# ---------------------------------------------------------------------------
# Handler exception tests
# ---------------------------------------------------------------------------


def test_tools_call_value_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("bad_tool", ValueError("bad input"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {"name": "bad_tool", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "ValueError" in resp["result"]["content"][0]["text"]
    assert "bad input" in resp["result"]["content"][0]["text"]


def test_tools_call_permission_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("restricted_tool", PermissionError("access denied"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {"name": "restricted_tool", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "PermissionError" in resp["result"]["content"][0]["text"]
    assert "access denied" in resp["result"]["content"][0]["text"]


def test_tools_call_runtime_error_returns_is_error(store: MemoryStore) -> None:
    tool = _raising_tool("crasher", RuntimeError("unexpected failure"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {"name": "crasher", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp["result"]["isError"] is True
    assert "RuntimeError" in resp["result"]["content"][0]["text"]


def test_tools_call_handler_exception_response_is_valid_jsonrpc(store: MemoryStore) -> None:
    tool = _raising_tool("flakey", OSError("disk full"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {"name": "flakey", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    # The envelope must be a valid JSON-RPC 2.0 result, not an error frame.
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 13
    assert "result" in resp
    assert "error" not in resp
    assert resp["result"]["isError"] is True


def test_tools_call_handler_exception_does_not_propagate(store: MemoryStore) -> None:
    # handle_request must never let a handler exception bubble up to the caller.
    tool = _raising_tool("boom", Exception("internal boom"))
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {"name": "boom", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert resp is not None
    assert resp["result"]["isError"] is True


def test_tools_call_learn_invalid_value_returns_is_error(store: MemoryStore) -> None:
    # The built-in `learn` tool raises ValueError for blank input; verify this
    # surfaces as isError rather than a server crash.
    resp = handle_request(
        {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {"name": "learn", "arguments": {"value": "   "}},
        },
        store,
    )
    assert resp["result"]["isError"] is True
    assert "ValueError" in resp["result"]["content"][0]["text"]


def test_tools_call_notification_with_handler_exception_returns_none(store: MemoryStore) -> None:
    # Notifications (no "id") must return None even when the handler would fail.
    tool = _raising_tool("noisy_notif", RuntimeError("boom"))
    result = handle_request(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "noisy_notif", "arguments": {}},
        },
        store,
        tools=(tool,),
    )
    assert result is None


def test_notification_for_unknown_method_returns_none(store: MemoryStore) -> None:
    # A notification (no "id") with an unknown method (not ping, not tools/*,
    # not notifications/*) must return None — not an error frame.
    result = handle_request({"jsonrpc": "2.0", "method": "completely_unknown_method"}, store)
    assert result is None


def test_serve_skips_blank_lines(store: MemoryStore) -> None:
    """serve() must silently skip blank / whitespace-only input lines."""
    import io

    stdin = io.StringIO('\n   \n{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n\n')
    stdout = io.StringIO()
    serve(store=store, stdin=stdin, stdout=stdout)
    lines = [line for line in stdout.getvalue().splitlines() if line.strip()]
    assert len(lines) == 1
    import json

    assert json.loads(lines[0])["id"] == 1


def test_serve_creates_and_closes_own_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When no store is passed, serve() creates its own and closes it on exit."""
    import io

    from sakthai.config import memory_db_path

    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))
    stdin = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n')
    stdout = io.StringIO()
    serve(stdin=stdin, stdout=stdout)  # no store= argument → own_store=True
    # The DB should now exist (was opened and closed by serve)
    assert memory_db_path().exists()
