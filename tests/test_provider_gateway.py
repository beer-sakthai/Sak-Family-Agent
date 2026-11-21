"""Tests for sakthai.agent.providers.gateway_provider and gateway loop integration."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.loop import _agent_turn
from sakthai.agent.providers import _build_gateway_client, _detect_from_client_type, detect_provider
from sakthai.agent.providers.base import Block, Response
from sakthai.agent.providers.gateway_provider import call_gateway
from sakthai.agent.tools import Tool
from sakthai.agent.usage import UsageTracker
from sakthai.client.gateway import GatewayClient


def _tool(name: str = "read_file") -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
        handler=lambda args, store: "content",
    )


def test_call_gateway_with_post_client() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {"message": {"content": "Gateway response", "tool_calls": []}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 8},
    }
    client = MagicMock(spec=["post"])
    client.post.return_value = mock_resp

    resp = call_gateway(
        client=client,
        model="sakthai",
        system="system prompt",
        messages=[{"role": "user", "content": "hello"}],
        tools=(_tool(),),
    )

    assert isinstance(resp, Response)
    assert resp.stop_reason == "end_turn"
    assert len(resp.content) == 1
    assert resp.content[0].text == "Gateway response"
    assert resp.usage["input_tokens"] == 12
    assert resp.usage["output_tokens"] == 8


def test_call_gateway_with_gateway_client() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "function": {
                                "name": "read_file",
                                "arguments": json.dumps({"path": "foo.txt"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 15, "completion_tokens": 5},
    }
    mock_httpx.post.return_value = mock_resp

    gw_client = GatewayClient(base_url="http://127.0.0.1:8080", httpx_client=mock_httpx)
    resp = call_gateway(
        client=gw_client,
        model="sakthai",
        system="system",
        messages=[{"role": "user", "content": "read foo"}],
        tools=(_tool(),),
    )

    assert resp.stop_reason == "tool_use"
    assert len(resp.content) == 1
    assert resp.content[0].type == "tool_use"
    assert resp.content[0].name == "read_file"
    assert resp.content[0].input == {"path": "foo.txt"}
    gw_client.close()


def test_detect_gateway_client_type() -> None:
    client = GatewayClient()
    detected = _detect_from_client_type(client)
    assert detected == "gateway"
    client.close()


def test_detect_provider_gateway_model() -> None:
    detected = detect_provider(None, model="gateway:sakthai")
    assert detected == "gateway"


def test_build_gateway_client_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "http://127.0.0.1:8080")
    monkeypatch.setenv("SAKTHAI_GATEWAY_TOKEN", "test-token")

    client = _build_gateway_client()
    assert isinstance(client, GatewayClient)
    assert client.base_url == "http://127.0.0.1:8080"
    assert client.api_token == "test-token"
    client.close()


def test_loop_step_routes_gateway() -> None:
    usage = UsageTracker()
    mock_client = MagicMock()
    expected_resp = Response(
        "end_turn", [Block("text", text="response")], {"input_tokens": 1, "output_tokens": 2}
    )

    with patch("sakthai.agent.loop._call_gateway", return_value=expected_resp) as mock_call:
        res = _agent_turn(
            provider="gateway",
            client=mock_client,
            model="sakthai",
            max_tokens=1000,
            system="system",
            tools=(),
            tool_schemas=[],
            messages=[{"role": "user", "content": "hi"}],
            iteration=1,
            on_token=None,
            usage_tracker=usage,
        )

        mock_call.assert_called_once()
        assert res.stop_reason == "end_turn"
        assert usage.input_tokens == 1
        assert usage.output_tokens == 2
