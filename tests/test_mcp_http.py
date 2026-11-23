"""The inbound MCP Streamable HTTP transport.

`handle_http` is a pure function over one parsed JSON-RPC body, for the same
reason `mcp/server.handle_request` is: the transport is testable without
opening a socket. These tests cover the parts HTTP adds — session identity,
header validation, the Origin check, and the status mapping — plus the
confirmation filter, which exists because an HTTP endpoint has no parent host
to ask the operator anything.
"""

from __future__ import annotations

import pytest

from sakthai.agent.tools import BUILTIN_TOOLS
from sakthai.mcp.http import (
    SESSION_HEADER,
    MCPSessionStore,
    confirmation_tools_allowed,
    handle_http,
    handle_http_delete,
    http_tools,
    origin_is_allowed,
)
from sakthai.mcp.protocol import LATEST_PROTOCOL_VERSION
from sakthai.memory.store import MemoryStore

INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}


@pytest.fixture
def sessions() -> MCPSessionStore:
    return MCPSessionStore()


def _init(store: MemoryStore, sessions: MCPSessionStore) -> str:
    """Run a handshake and return the minted session id."""
    result = handle_http(INIT, store, sessions=sessions)
    assert result.status == 200
    return result.headers[SESSION_HEADER]


# --- the handshake and sessions ---------------------------------------------


def test_initialize_mints_a_session(store: MemoryStore, sessions: MCPSessionStore) -> None:
    result = handle_http(INIT, store, sessions=sessions)
    assert result.status == 200
    assert result.headers[SESSION_HEADER]
    assert result.payload["result"]["protocolVersion"] == LATEST_PROTOCOL_VERSION
    assert len(sessions) == 1


def test_a_known_session_is_accepted(store: MemoryStore, sessions: MCPSessionStore) -> None:
    session_id = _init(store, sessions)
    result = handle_http(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        store,
        sessions=sessions,
        session_id=session_id,
    )
    assert result.status == 200
    assert "tools" in result.payload["result"]


def test_an_unknown_session_is_404(store: MemoryStore, sessions: MCPSessionStore) -> None:
    """The spec's recovery path: the client re-initializes."""
    result = handle_http(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        store,
        sessions=sessions,
        session_id="made-up",
    )
    assert result.status == 404
    assert result.payload["error"] == "session_not_found"


def test_a_request_without_a_session_header_is_served(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    """Sessions are optional for a server that keeps no state between calls."""
    result = handle_http({"jsonrpc": "2.0", "id": 2, "method": "ping"}, store, sessions=sessions)
    assert result.status == 200


def test_delete_terminates_a_session(store: MemoryStore, sessions: MCPSessionStore) -> None:
    session_id = _init(store, sessions)
    assert handle_http_delete(session_id, sessions=sessions).status == 204
    assert len(sessions) == 0


def test_delete_of_an_unknown_session_is_404(sessions: MCPSessionStore) -> None:
    assert handle_http_delete("nope", sessions=sessions).status == 404


def test_delete_without_a_session_header_is_400(sessions: MCPSessionStore) -> None:
    """It asks to end something it has not named."""
    result = handle_http_delete(None, sessions=sessions)
    assert result.status == 400
    assert result.payload["error"] == "missing_session"


# --- the session store ------------------------------------------------------


def test_idle_sessions_expire() -> None:
    store = MCPSessionStore(idle_seconds=-1.0)
    session_id = store.create(LATEST_PROTOCOL_VERSION)
    assert store.touch(session_id) is None


def test_session_count_is_bounded() -> None:
    """An unauthenticated flood must not grow the map without bound."""
    store = MCPSessionStore(max_sessions=3)
    ids = [store.create(LATEST_PROTOCOL_VERSION) for _ in range(5)]
    assert len(store) <= 3
    # The newest survive; the oldest were evicted.
    assert store.touch(ids[-1]) is not None


def test_terminate_is_idempotent() -> None:
    store = MCPSessionStore()
    session_id = store.create(LATEST_PROTOCOL_VERSION)
    assert store.terminate(session_id) is True
    assert store.terminate(session_id) is False


# --- protocol version header ------------------------------------------------


def test_a_supported_version_header_is_accepted(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    result = handle_http(INIT, store, sessions=sessions, protocol_version="2024-11-05")
    assert result.status == 200


def test_an_unsupported_version_header_is_400(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    result = handle_http(INIT, store, sessions=sessions, protocol_version="2026-07-28")
    assert result.status == 400
    assert result.payload["error"] == "unsupported_protocol_version"
    # The error names what we do speak, so the client can retry usefully.
    assert "2025-11-25" in result.payload["message"]


def test_a_missing_version_header_is_accepted(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    """Required only from 2025-06-18; an older client sends none."""
    assert handle_http(INIT, store, sessions=sessions, protocol_version=None).status == 200


# --- Origin / DNS rebinding -------------------------------------------------


@pytest.mark.parametrize(
    "origin",
    [None, "", "http://localhost:3000", "http://127.0.0.1:8080", "https://[::1]:443"],
)
def test_loopback_and_absent_origins_are_allowed(origin: str | None) -> None:
    assert origin_is_allowed(origin)


@pytest.mark.parametrize("origin", ["https://evil.example", "http://attacker.test:8080"])
def test_foreign_origins_are_rejected(origin: str) -> None:
    assert not origin_is_allowed(origin)


def test_an_allowlisted_origin_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_HTTP_ORIGIN", "dash.example")
    assert origin_is_allowed("https://dash.example")


def test_a_foreign_origin_gets_403(store: MemoryStore, sessions: MCPSessionStore) -> None:
    result = handle_http(INIT, store, sessions=sessions, origin="https://evil.example")
    assert result.status == 403
    assert len(sessions) == 0  # no session minted for a rejected request


def test_an_unparseable_origin_is_rejected() -> None:
    assert not origin_is_allowed("not a url")


# --- the confirmation filter ------------------------------------------------


def test_confirmation_tools_are_hidden_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """No parent host exists over HTTP to ask the operator anything."""
    monkeypatch.delenv("SAKTHAI_MCP_HTTP_WRITE_ALLOW", raising=False)
    assert not confirmation_tools_allowed()
    names = {t.name for t in http_tools()}
    assert "run_command" not in names
    assert "write_file" not in names
    assert "run_agent_loop" not in names
    # Read-only tools are unaffected.
    assert "recall" in names
    assert "search" in names


def test_the_opt_in_exposes_them(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_HTTP_WRITE_ALLOW", "1")
    assert confirmation_tools_allowed()
    assert http_tools() == BUILTIN_TOOLS


def test_the_filter_matches_requires_confirmation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_HTTP_WRITE_ALLOW", raising=False)
    hidden = {t.name for t in BUILTIN_TOOLS} - {t.name for t in http_tools()}
    assert hidden == {t.name for t in BUILTIN_TOOLS if t.requires_confirmation}
    assert hidden, "no tool is marked requires_confirmation; the filter tests nothing"


def test_a_filtered_tool_is_not_listed_over_http(
    store: MemoryStore, sessions: MCPSessionStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_HTTP_WRITE_ALLOW", raising=False)
    result = handle_http(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, store, sessions=sessions
    )
    assert "run_command" not in {t["name"] for t in result.payload["result"]["tools"]}


def test_a_filtered_tool_cannot_be_called_over_http(
    store: MemoryStore, sessions: MCPSessionStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_HTTP_WRITE_ALLOW", raising=False)
    result = handle_http(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "run_command", "arguments": {"command": "ls"}},
        },
        store,
        sessions=sessions,
    )
    assert result.payload["result"]["isError"] is True
    assert "Unknown tool" in result.payload["result"]["content"][0]["text"]


# --- notifications and batches ----------------------------------------------


def test_a_notification_earns_202_with_no_body(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    result = handle_http(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}, store, sessions=sessions
    )
    assert result.status == 202
    assert result.payload is None


def test_a_batch_returns_a_list(store: MemoryStore, sessions: MCPSessionStore) -> None:
    """Revisions before 2025-06-18 permit JSON-RPC batching."""
    result = handle_http(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "ping"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ],
        store,
        sessions=sessions,
    )
    assert result.status == 200
    assert isinstance(result.payload, list)
    assert [r["id"] for r in result.payload] == [1, 2]


def test_a_batch_of_notifications_earns_202(store: MemoryStore, sessions: MCPSessionStore) -> None:
    result = handle_http(
        [{"jsonrpc": "2.0", "method": "notifications/initialized"}], store, sessions=sessions
    )
    assert result.status == 202


def test_an_empty_batch_is_400(store: MemoryStore, sessions: MCPSessionStore) -> None:
    result = handle_http([], store, sessions=sessions)
    assert result.status == 400


def test_a_single_message_returns_an_object_not_a_list(
    store: MemoryStore, sessions: MCPSessionStore
) -> None:
    result = handle_http({"jsonrpc": "2.0", "id": 1, "method": "ping"}, store, sessions=sessions)
    assert isinstance(result.payload, dict)


def test_garbage_gets_a_jsonrpc_error(store: MemoryStore, sessions: MCPSessionStore) -> None:
    result = handle_http("not a message", store, sessions=sessions)
    assert result.status == 200
    assert result.payload["error"]["code"] == -32600
