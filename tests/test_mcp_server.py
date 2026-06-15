"""Tests for the MCP JSON-RPC request handler and stdio loop."""

from __future__ import annotations

import io
import json

from sakthai.mcp.server import PROTOCOL_VERSION, handle_request, serve
from sakthai.memory.store import MemoryStore


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
