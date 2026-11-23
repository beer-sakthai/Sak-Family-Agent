"""End-to-end: the MCP Streamable HTTP endpoint over a real socket.

`tests/test_mcp_http.py` covers the transport logic as a pure function. This
covers the wiring — that the gateway routes `/v1/mcp`, carries the session and
protocol headers both ways, enforces its bearer token, and honours DELETE.

It is hosted on the gateway rather than `web/server.py` because the gateway is
already a `ThreadingHTTPServer` with POST and DELETE, while the web API serves
GET and HEAD only and is byte-parity copied into all six personas.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.server import RuntimeGatewayServer
from sakthai.mcp.http import SESSION_HEADER
from sakthai.mcp.protocol import LATEST_PROTOCOL_VERSION, PROTOCOL_VERSION_HEADER

TOKEN = "mcp-endpoint-test-token"  # nosec B105 — test fixture, not a credential


def _post(
    url: str,
    body: Any,
    headers: dict[str, str] | None = None,
    method: str = "POST",
) -> tuple[int, Any, dict[str, str]]:
    req_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:  # nosec B310
            raw = resp.read().decode("utf-8")
            out_headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, (json.loads(raw) if raw else None), out_headers
    except urllib.error.HTTPError as err:
        raw = err.read().decode("utf-8")
        out_headers = {k.lower(): v for k, v in err.headers.items()}
        try:
            return err.code, json.loads(raw), out_headers
        except json.JSONDecodeError:
            return err.code, raw, out_headers


@pytest.fixture
def mcp_server() -> Iterator[RuntimeGatewayServer]:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token=TOKEN)
    server = RuntimeGatewayServer(config=cfg)
    server.start(background=True)
    yield server
    server.shutdown()


@pytest.fixture
def mcp_url(mcp_server: RuntimeGatewayServer) -> str:
    return f"http://127.0.0.1:{mcp_server.port}/v1/mcp"


def test_initialize_over_http(mcp_url: str) -> None:
    status, body, headers = _post(
        mcp_url,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert status == 200
    assert body["result"]["protocolVersion"] == LATEST_PROTOCOL_VERSION
    assert body["result"]["serverInfo"]["name"] == "sakthai"
    assert headers[SESSION_HEADER.lower()]


def test_tools_list_over_http(mcp_url: str) -> None:
    _, _, headers = _post(mcp_url, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    session = headers[SESSION_HEADER.lower()]

    status, body, _ = _post(
        mcp_url,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {SESSION_HEADER: session, PROTOCOL_VERSION_HEADER: LATEST_PROTOCOL_VERSION},
    )
    assert status == 200
    names = {t["name"] for t in body["result"]["tools"]}
    assert {"recall", "search"} <= names
    # The confirmation filter is on by default over HTTP.
    assert "run_command" not in names


def test_a_tool_call_round_trips(mcp_url: str) -> None:
    _, _, headers = _post(mcp_url, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    session = headers[SESSION_HEADER.lower()]

    status, body, _ = _post(
        mcp_url,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "recall", "arguments": {"limit": 1}},
        },
        {SESSION_HEADER: session},
    )
    assert status == 200
    assert body["result"]["isError"] is False


def test_an_unknown_session_is_404(mcp_url: str) -> None:
    status, body, _ = _post(
        mcp_url,
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        {SESSION_HEADER: "fabricated"},
    )
    assert status == 404
    assert body["error"] == "session_not_found"


def test_delete_terminates_the_session(mcp_url: str) -> None:
    _, _, headers = _post(mcp_url, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    session = headers[SESSION_HEADER.lower()]

    status, _, _ = _post(mcp_url, None, {SESSION_HEADER: session}, method="DELETE")
    assert status == 204

    status, _, _ = _post(
        mcp_url, {"jsonrpc": "2.0", "id": 2, "method": "ping"}, {SESSION_HEADER: session}
    )
    assert status == 404


def test_an_unsupported_protocol_header_is_400(mcp_url: str) -> None:
    status, body, _ = _post(
        mcp_url,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        {PROTOCOL_VERSION_HEADER: "2026-07-28"},
    )
    assert status == 400
    assert body["error"] == "unsupported_protocol_version"


def test_a_foreign_origin_is_403(mcp_url: str) -> None:
    """DNS-rebinding defence: a page on another domain must not reach this."""
    status, _, _ = _post(
        mcp_url,
        {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        {"Origin": "https://evil.example"},
    )
    assert status == 403


def test_a_notification_is_202(mcp_url: str) -> None:
    status, body, _ = _post(mcp_url, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert status == 202
    assert body is None


def test_the_endpoint_requires_the_bearer_token(mcp_url: str) -> None:
    req = urllib.request.Request(
        mcp_url,
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as caught:
        urllib.request.urlopen(req, timeout=5.0)  # nosec B310
    assert caught.value.code == 401


def test_the_bare_mcp_path_also_routes(mcp_server: RuntimeGatewayServer) -> None:
    status, body, _ = _post(
        f"http://127.0.0.1:{mcp_server.port}/mcp",
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
    )
    assert status == 200
    assert body["result"] == {}
