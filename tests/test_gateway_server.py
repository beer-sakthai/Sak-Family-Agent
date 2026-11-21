"""Unit and integration tests for the live Runtime Gateway HTTP server."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.server import RuntimeGatewayServer


def _http_request(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    raw_body: bytes | None = None,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    data = (
        raw_body
        if raw_body is not None
        else (json.dumps(body).encode("utf-8") if body is not None else None)
    )
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:  # nosec B310
            resp_headers = {k: v for k, v in resp.headers.items()}
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw), resp_headers
            except json.JSONDecodeError:
                return resp.status, raw, resp_headers
    except urllib.error.HTTPError as err:
        resp_headers = {k: v for k, v in err.headers.items()}
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw), resp_headers
        except Exception:
            return err.code, raw, resp_headers


@pytest.fixture
def running_server() -> RuntimeGatewayServer:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token="test-secret-token")
    server = RuntimeGatewayServer(config=cfg)
    server.start(background=True)
    yield server
    server.shutdown()


def test_server_health_unauthenticated(running_server: RuntimeGatewayServer) -> None:
    url = f"http://127.0.0.1:{running_server.port}/health"
    status, data, _ = _http_request(url)
    assert status == 200
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert data["gateway"] == "running"


def test_server_auth_enforcement(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"

    # Missing auth -> 401
    status, data, _ = _http_request(f"{base}/v1/models")
    assert status == 401

    # Valid Bearer header -> 200
    status, data, _ = _http_request(
        f"{base}/v1/models",
        headers={"Authorization": "Bearer test-secret-token"},
    )
    assert status == 200
    assert isinstance(data, dict)
    assert "data" in data

    # Valid query string -> 200
    status, data, _ = _http_request(f"{base}/v1/models?token=test-secret-token")
    assert status == 200


def test_server_personas_and_details(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    # List personas
    status, data, _ = _http_request(f"{base}/v1/personas", headers=headers)
    assert status == 200
    assert isinstance(data, dict)
    assert data["count"] == 6

    # Detail valid
    status, data, _ = _http_request(f"{base}/v1/personas/sakking", headers=headers)
    assert status == 200
    assert isinstance(data, dict)
    assert data["name"] == "SakKing"

    # Detail invalid -> 404
    status, data, _ = _http_request(f"{base}/v1/personas/unknown", headers=headers)
    assert status == 404


def test_server_tools_and_execution(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    # List tools
    status, data, _ = _http_request(f"{base}/v1/tools", headers=headers)
    assert status == 200
    assert isinstance(data, dict)
    assert "tools" in data

    # Execute tool (blocked by guardrail)
    status, data, _ = _http_request(
        f"{base}/v1/tools/execute",
        method="POST",
        body={"tool": "run_command", "arguments": {"command": "rm -rf /"}},
        headers=headers,
    )
    assert status == 200
    assert isinstance(data, dict)
    assert data["status"] == "blocked"


def test_server_chat_completions_non_streaming(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    body = {
        "model": "sakthai",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False,
    }
    status, data, _ = _http_request(
        f"{base}/v1/chat/completions",
        method="POST",
        body=body,
        headers=headers,
    )
    assert status == 200
    assert isinstance(data, dict)
    assert data["object"] == "chat.completion"
    assert "choices" in data


def test_server_chat_completions_streaming(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    body = {
        "model": "sakthai",
        "messages": [{"role": "user", "content": "Count to three"}],
        "stream": True,
    }
    status, data, resp_headers = _http_request(
        f"{base}/v1/chat/completions",
        method="POST",
        body=body,
        headers=headers,
    )
    assert status == 200
    assert "text/event-stream" in resp_headers.get("Content-Type", "")
    assert isinstance(data, str)
    assert "data: " in data
    assert "[DONE]" in data


def test_server_cors_options(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    status, _, headers = _http_request(f"{base}/v1/chat/completions", method="OPTIONS")
    assert status == 204
    assert headers.get("Access-Control-Allow-Origin") == "*"


def test_server_error_cases(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    # Unknown path GET
    status, _, _ = _http_request(f"{base}/unknown/path", headers=headers)
    assert status == 404

    # Unknown path POST
    status, _, _ = _http_request(f"{base}/unknown/post", method="POST", body={}, headers=headers)
    assert status == 404

    # Malformed JSON
    status, data, _ = _http_request(
        f"{base}/v1/chat/completions",
        method="POST",
        raw_body=b"{malformed json",
        headers=headers,
    )
    assert status == 400
    assert "Malformed JSON" in str(data)

    # Missing messages
    status, data, _ = _http_request(
        f"{base}/v1/chat/completions",
        method="POST",
        body={"model": "sakthai"},
        headers=headers,
    )
    assert status == 400
    assert "messages" in str(data)


def test_server_context_manager() -> None:
    cfg = GatewayConfig(host="127.0.0.1", port=0)
    with RuntimeGatewayServer(config=cfg) as s:
        assert s.is_running
        assert s.port > 0
        # start when already running is no-op
        s.start(background=True)
    assert not s.is_running
    # shutdown when already stopped is no-op
    s.shutdown()


def test_server_chat_completions_unexpected_error(
    running_server: RuntimeGatewayServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    def failing_chat(body: Any) -> Any:
        raise RuntimeError("Unexpected failure")

    monkeypatch.setattr(running_server.router, "handle_chat_completion", failing_chat)

    body = {"model": "sakthai", "messages": [{"role": "user", "content": "hello"}]}
    status, data, _ = _http_request(
        f"{base}/v1/chat/completions", method="POST", body=body, headers=headers
    )
    assert status == 500
    assert "Internal execution error" in str(data)


def test_server_tools_execute_error_status(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    status, data, _ = _http_request(
        f"{base}/v1/tools/execute", method="POST", body={}, headers=headers
    )
    assert status == 400
    assert "Missing required field" in str(data)


def test_server_open_access_mode() -> None:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token=None)
    with RuntimeGatewayServer(config=cfg) as server:
        status, data, _ = _http_request(f"http://127.0.0.1:{server.port}/v1/models")
        assert status == 200
        assert isinstance(data, dict)
        assert "data" in data


def test_server_root_path_and_unauthenticated_post(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    # Root path GET -> 404
    status, _, _ = _http_request(f"{base}/", headers=headers)
    assert status == 404

    # Unauthenticated POST -> 401
    status, _, _ = _http_request(
        f"{base}/v1/chat/completions",
        method="POST",
        body={"model": "sakthai", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert status == 401


def test_server_api_compatibility_endpoints(running_server: RuntimeGatewayServer) -> None:
    base = f"http://127.0.0.1:{running_server.port}"
    headers = {"Authorization": "Bearer test-secret-token"}

    # /api/status
    status, data, _ = _http_request(f"{base}/api/status", headers=headers)
    assert status == 200
    assert isinstance(data, dict)
    assert data.get("status") == "ok"

    # /api/saksee/status
    status, data, _ = _http_request(f"{base}/api/saksee/status", headers=headers)
    assert status == 200
    assert isinstance(data, dict)
    assert data.get("telegram") == "connected"

    # /api/model/chat
    status, data, _ = _http_request(
        f"{base}/api/model/chat",
        method="POST",
        body={"prompt": "Ping"},
        headers=headers,
    )
    assert status == 200
    assert isinstance(data, dict)
    assert "response" in data


def test_server_start_foreground_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = GatewayConfig(host="127.0.0.1", port=0)
    server = RuntimeGatewayServer(config=cfg)

    def mock_serve_forever(self_httpd: Any) -> None:
        return

    monkeypatch.setattr(
        "sakthai.gateway.server._GatewayHTTPServer.serve_forever", mock_serve_forever
    )
    server.start(background=False)
    assert not server.is_running


def test_request_handler_log_message() -> None:
    from unittest.mock import MagicMock

    from sakthai.gateway.server import GatewayRequestHandler

    handler = GatewayRequestHandler.__new__(GatewayRequestHandler)
    handler.address_string = MagicMock(return_value="127.0.0.1")  # type: ignore[method-assign]
    handler.log_date_time_string = MagicMock(return_value="01/Jan/2026:00:00:00")  # type: ignore[method-assign]
    handler.log_message("GET %s %d", "/test", 200)
