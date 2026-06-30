"""Real-subprocess resilience tests for the outbound MCP stdio client.

The existing ``test_mcp_client.py`` suite either drives SakThai's own well-behaved
MCP server or stubs ``_readline`` with a lambda. Neither exercises the
``select``-based read loop in :meth:`StdioMCPClient._readline` /
``_read_response`` against a *real* OS pipe feeding *misbehaving* output — which
is exactly where the dependency-free, hand-rolled JSON-RPC plumbing is most
likely to break (line buffering, EOF detection, id matching, timeouts).

Each test launches a tiny fake MCP server (this same interpreter running an
inline script) whose behaviour is selected by the ``FAKE_MODE`` env var, then
asserts the client copes. No network; the only process spawned is ``python``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sakthai.mcp.client import MCPClientError, StdioMCPClient

# A minimal JSON-RPC-over-stdio MCP server. It completes the handshake, then
# misbehaves on tools/call according to FAKE_MODE so each test can target one
# failure mode. Kept dependency-free and synchronous to mirror the client.
FAKE_SERVER = r"""
import sys, json, os, time

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

mode = os.environ.get("FAKE_MODE", "ok")
TOOL = {"name": "echo", "description": "echo", "inputSchema": {"type": "object"}}

for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
        continue
    msg = json.loads(raw)
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": mid,
              "result": {"protocolVersion": "2024-11-05", "capabilities": {}}})
        if mode == "die_after_init":
            sys.exit(0)
    elif method == "notifications/initialized":
        continue
    elif method == "tools/list":
        send({"jsonrpc": "2.0", "id": mid, "result": {"tools": [TOOL]}})
    elif method == "tools/call":
        if mode == "garbage_then_valid":
            sys.stdout.write("this is not json at all\n")
            sys.stdout.write("   \n")
            sys.stdout.write("<<< more noise >>>\n")
            sys.stdout.flush()
            send({"jsonrpc": "2.0", "id": mid,
                  "result": {"content": [{"type": "text", "text": "recovered"}]}})
        elif mode == "wrong_id_then_right":
            send({"jsonrpc": "2.0", "id": 99999,
                  "result": {"content": [{"type": "text", "text": "stale"}]}})
            send({"jsonrpc": "2.0", "id": mid,
                  "result": {"content": [{"type": "text", "text": "correct"}]}})
        elif mode == "notifications_flood":
            for i in range(25):
                send({"jsonrpc": "2.0", "method": "notifications/progress",
                      "params": {"n": i}})
            send({"jsonrpc": "2.0", "id": mid,
                  "result": {"content": [{"type": "text", "text": "after-flood"}]}})
        elif mode == "hang":
            time.sleep(60)
        elif mode == "die_mid_call":
            sys.exit(0)
        else:
            send({"jsonrpc": "2.0", "id": mid,
                  "result": {"content": [{"type": "text", "text": "ok"}]}})
"""


def _client(tmp_path: Path, mode: str, *, timeout: float = 10.0) -> StdioMCPClient:
    script = tmp_path / "fake_mcp_server.py"
    script.write_text(FAKE_SERVER, encoding="utf-8")
    return StdioMCPClient(
        sys.executable,
        [str(script)],
        env={"FAKE_MODE": mode},
        name="fake",
        timeout=timeout,
    )


def test_handshake_against_real_fake_server(tmp_path: Path) -> None:
    with _client(tmp_path, "ok") as client:
        assert [t["name"] for t in client.list_tools()] == ["echo"]
        assert client.call_tool("echo", {"x": 1}) == "ok"


def test_non_json_noise_before_response_is_skipped(tmp_path: Path) -> None:
    # The real readline loop must drop garbage lines and keep reading until the
    # matching JSON-RPC response arrives on the pipe.
    with _client(tmp_path, "garbage_then_valid") as client:
        assert client.call_tool("echo", {}) == "recovered"


def test_unrelated_id_is_skipped_until_matching_reply(tmp_path: Path) -> None:
    # A response for a different id must not be mistaken for ours.
    with _client(tmp_path, "wrong_id_then_right") as client:
        assert client.call_tool("echo", {}) == "correct"


def test_notification_flood_before_response(tmp_path: Path) -> None:
    # Interleaved notifications (no id) must be ignored, not blocked on.
    with _client(tmp_path, "notifications_flood") as client:
        assert client.call_tool("echo", {}) == "after-flood"


def test_hung_server_times_out(tmp_path: Path) -> None:
    # A server that never replies must trip the select timeout, not block forever.
    with (
        _client(tmp_path, "hang", timeout=1.0) as client,
        pytest.raises(MCPClientError, match="timed out"),
    ):
        client.call_tool("echo", {})


def test_server_death_mid_call_fails_loudly(tmp_path: Path) -> None:
    # EOF on stdout while awaiting a reply must raise, not hang or return empty.
    with (
        _client(tmp_path, "die_mid_call") as client,
        pytest.raises(MCPClientError, match="closed before responding"),
    ):
        client.call_tool("echo", {})


def test_server_death_mid_handshake_fails_to_start(tmp_path: Path) -> None:
    # Dying right after initialize (before tools/list) must fail start(), not
    # leave a half-initialised client.
    client = _client(tmp_path, "die_after_init", timeout=5.0)
    with pytest.raises(MCPClientError):
        client.start()
    client.close()
