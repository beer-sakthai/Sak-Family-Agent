"""Tests for Work IQ MCP client and tool allowlist filtering."""

from __future__ import annotations

import httpx
import pytest
from sak_mcp_gateway.work_iq_client import WorkIQClient, WorkIQSecurityError


def test_is_tool_allowed_read_only() -> None:
    client = WorkIQClient()
    assert client.is_tool_allowed("retrieve") is True
    assert client.is_tool_allowed("search") is True
    assert client.is_tool_allowed("find") is True
    assert client.is_tool_allowed("list") is True
    assert client.is_tool_allowed("summarize") is True


def test_is_tool_allowed_blocks_mutations() -> None:
    client = WorkIQClient()
    assert client.is_tool_allowed("create_email") is False
    assert client.is_tool_allowed("delete_file") is False
    assert client.is_tool_allowed("update_contact") is False
    assert client.is_tool_allowed("send_message") is False
    assert client.is_tool_allowed("write_document") is False
    assert client.is_tool_allowed("modify_permission") is False
    assert client.is_tool_allowed("post_channel_message") is False


def test_filter_tools() -> None:
    client = WorkIQClient()
    remote_tools = [
        {"name": "retrieve", "description": "Safe read"},
        {"name": "create_event", "description": "Mutating write"},
        {"name": "search", "description": "Safe query"},
        {"name": "delete_event", "description": "Mutating delete"},
    ]
    safe_tools = client.filter_tools(remote_tools)
    safe_names = [t["name"] for t in safe_tools]
    assert safe_names == ["retrieve", "search"]


@pytest.mark.asyncio
async def test_retrieve_blocked_raises_security_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = WorkIQClient()
    monkeypatch.setattr(client, "is_tool_allowed", lambda _tool: False)
    with pytest.raises(WorkIQSecurityError, match="not permitted"):
        await client.retrieve("test query")


@pytest.mark.asyncio
async def test_retrieve_calls_endpoint() -> None:
    called = {}

    def handler(request: httpx.Request) -> httpx.Response:
        called["url"] = str(request.url)
        called["headers"] = dict(request.headers)
        return httpx.Response(
            200, json={"jsonrpc": "2.0", "id": 1, "result": {"content": [{"text": "result"}]}}
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http_client:
        client = WorkIQClient(
            endpoint="https://mock.workiq/mcp", user_bearer_token="mock-token-xyz"
        )
        res = await client.retrieve("What are my meetings today?", client=http_client)
        assert res["result"]["content"][0]["text"] == "result"
        assert called["url"] == "https://mock.workiq/mcp"
        assert called["headers"]["authorization"] == "Bearer mock-token-xyz"
