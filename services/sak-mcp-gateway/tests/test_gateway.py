"""Tests for FastAPI MCP endpoint in sak_mcp_gateway."""

from __future__ import annotations

import json

import jwt
import pytest
from fastapi.testclient import TestClient
from sak_mcp_gateway.config import GatewayConfig
from sak_mcp_gateway.gateway import create_app


@pytest.fixture
def test_client() -> TestClient:
    cfg = GatewayConfig(
        entra_tenant_id="test-tenant",
        entra_audience="api://test-audience",
        entra_required_scope="Sak.Read",
        public_host="mcp.example.com",
        mock_auth=True,
    )
    app = create_app(cfg)
    return TestClient(app)


@pytest.fixture
def valid_auth_headers() -> dict[str, str]:
    payload = {
        "aud": "api://test-audience",
        "sub": "user-456",
        "scp": "Sak.Read",
    }
    token = jwt.encode(payload, "mock-test-secret-key-with-at-least-32-bytes!", algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(test_client: TestClient) -> None:
    resp = test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sak-mcp-gateway"
    assert data["public_host"] == "mcp.example.com"


def test_mcp_without_auth_header_fails(test_client: TestClient) -> None:
    resp = test_client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert resp.status_code == 401
    assert "Missing Authorization" in resp.text


def test_mcp_with_invalid_auth_header_format(test_client: TestClient) -> None:
    resp = test_client.post(
        "/mcp",
        headers={"Authorization": "Basic 12345"},
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    )
    assert resp.status_code == 401
    assert "Expected 'Bearer <token>'" in resp.text


def test_mcp_initialize(test_client: TestClient, valid_auth_headers: dict[str, str]) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={"jsonrpc": "2.0", "id": 101, "method": "initialize"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 101
    assert data["result"]["serverInfo"]["name"] == "sak-mcp-gateway"
    assert "tools" in data["result"]["capabilities"]


def test_mcp_tools_list(test_client: TestClient, valid_auth_headers: dict[str, str]) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={"jsonrpc": "2.0", "id": 102, "method": "tools/list"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 102
    tools = data["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "sak_health_status" in tool_names
    assert "sak_family_catalog" in tool_names


def test_mcp_tools_call_health(test_client: TestClient, valid_auth_headers: dict[str, str]) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={
            "jsonrpc": "2.0",
            "id": 103,
            "method": "tools/call",
            "params": {"name": "sak_health_status", "arguments": {"verbose": True}},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 103
    assert data["result"]["isError"] is False
    content_text = data["result"]["content"][0]["text"]
    parsed_out = json.loads(content_text)
    assert parsed_out["ok"] is True
    assert parsed_out["status"] == "healthy"


def test_mcp_tools_call_catalog(
    test_client: TestClient, valid_auth_headers: dict[str, str]
) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={
            "jsonrpc": "2.0",
            "id": 104,
            "method": "tools/call",
            "params": {"name": "sak_family_catalog", "arguments": {"persona": "saksee"}},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 104
    assert data["result"]["isError"] is False
    content_text = data["result"]["content"][0]["text"]
    parsed_out = json.loads(content_text)
    assert "saksee" in parsed_out["personas"]


def test_mcp_tools_call_unknown(
    test_client: TestClient, valid_auth_headers: dict[str, str]
) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={
            "jsonrpc": "2.0",
            "id": 105,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 105
    assert data["result"]["isError"] is True


def test_mcp_unknown_method(test_client: TestClient, valid_auth_headers: dict[str, str]) -> None:
    resp = test_client.post(
        "/mcp",
        headers=valid_auth_headers,
        json={"jsonrpc": "2.0", "id": 106, "method": "nonexistent/method"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"]["code"] == -32601
