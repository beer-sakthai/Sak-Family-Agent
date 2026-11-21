"""Tests for sakthai.client.gateway — GatewayClient SDK."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sakthai.client.gateway import DEFAULT_GATEWAY_URL, GatewayClient, GatewayError


def test_gateway_client_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_GATEWAY_URL", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_GATEWAY_URL", raising=False)
    monkeypatch.delenv("SAKTHAI_GATEWAY_TOKEN", raising=False)
    monkeypatch.delenv("SAKTHAI_GATEWAY_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("SAKTHAI_API_TOKEN", raising=False)

    client = GatewayClient()
    assert client.base_url == DEFAULT_GATEWAY_URL
    assert client.api_token is None
    assert "Authorization" not in client.headers
    client.close()


def test_gateway_client_env_discovery(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "http://gateway.internal:9000/")
    monkeypatch.setenv("SAKTHAI_GATEWAY_TOKEN", "token-secret-123")

    client = GatewayClient()
    assert client.base_url == "http://gateway.internal:9000"
    assert client.api_token == "token-secret-123"
    assert client.headers["Authorization"] == "Bearer token-secret-123"
    client.close()


def test_gateway_client_context_manager() -> None:
    mock_httpx = MagicMock()
    with GatewayClient(httpx_client=mock_httpx) as client:
        assert client.base_url == DEFAULT_GATEWAY_URL
    mock_httpx.close.assert_called_once()


def test_gateway_client_health() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok", "uptime_seconds": 120}
    mock_resp.raise_for_status.return_value = None
    mock_httpx.get.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    result = client.health()

    mock_httpx.get.assert_called_once_with("/health")
    assert result["status"] == "ok"
    assert result["uptime_seconds"] == 120
    client.close()


def test_gateway_client_list_models() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "data": [{"id": "sakthai", "object": "model"}, {"id": "sakjules", "object": "model"}]
    }
    mock_resp.raise_for_status.return_value = None
    mock_httpx.get.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    models = client.list_models()

    mock_httpx.get.assert_called_once_with("/v1/models")
    assert len(models) == 2
    assert models[0]["id"] == "sakthai"
    client.close()


def test_gateway_client_list_personas() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"personas": [{"id": "sakthai", "name": "SakThai"}]}
    mock_resp.raise_for_status.return_value = None
    mock_httpx.get.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    personas = client.list_personas()

    mock_httpx.get.assert_called_once_with("/v1/personas")
    assert len(personas) == 1
    assert personas[0]["id"] == "sakthai"
    client.close()


def test_gateway_client_list_tools() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "tools": [{"type": "function", "function": {"name": "read_file"}}]
    }
    mock_resp.raise_for_status.return_value = None
    mock_httpx.get.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    tools = client.list_tools()

    mock_httpx.get.assert_called_once_with("/v1/tools")
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "read_file"
    client.close()


def test_gateway_client_execute_tool() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "success", "result": "hello world"}
    mock_httpx.post.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    res = client.execute_tool("read_file", {"path": "README.md"}, approval_token="token-abc")

    mock_httpx.post.assert_called_once_with(
        "/v1/tools/execute",
        json={
            "tool": "read_file",
            "arguments": {"path": "README.md"},
            "approval_token": "token-abc",
        },
    )
    assert res["status"] == "success"
    client.close()


def test_gateway_client_chat_completions() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Done."}}]
    }
    mock_httpx.post.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    res = client.chat_completions(
        [{"role": "user", "content": "Hi"}],
        model="sakthai:flash",
        tools=[{"type": "function", "function": {"name": "test"}}],
    )

    mock_httpx.post.assert_called_once()
    assert res["choices"][0]["message"]["content"] == "Done."
    client.close()


def test_gateway_client_chat_completions_error() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized token"
    mock_httpx.post.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    with pytest.raises(GatewayError, match="Gateway error 401: Unauthorized token"):
        client.chat_completions([{"role": "user", "content": "Hi"}])
    client.close()


def test_gateway_client_stream_chat() -> None:
    mock_httpx = MagicMock()
    mock_stream_resp = MagicMock()
    mock_stream_resp.status_code = 200
    mock_stream_resp.iter_lines.return_value = [
        "data: " + json.dumps({"choices": [{"delta": {"content": "Hello"}}]}),
        "",
        "invalid json line",
        "data: not json",
        "data: " + json.dumps({"choices": [{"delta": {"content": " world"}}]}),
        "data: [DONE]",
    ]

    mock_stream_context = MagicMock()
    mock_stream_context.__enter__.return_value = mock_stream_resp
    mock_httpx.stream.return_value = mock_stream_context

    client = GatewayClient(httpx_client=mock_httpx)
    chunks = list(client.stream_chat([{"role": "user", "content": "Hi"}]))

    assert len(chunks) == 2
    assert chunks[0]["choices"][0]["delta"]["content"] == "Hello"
    assert chunks[1]["choices"][0]["delta"]["content"] == " world"
    client.close()


def test_gateway_client_stream_chat_error() -> None:
    mock_httpx = MagicMock()
    mock_stream_resp = MagicMock()
    mock_stream_resp.status_code = 500
    mock_stream_resp.read.return_value = b"Internal gateway failure"

    mock_stream_context = MagicMock()
    mock_stream_context.__enter__.return_value = mock_stream_resp
    mock_httpx.stream.return_value = mock_stream_context

    client = GatewayClient(httpx_client=mock_httpx)
    with pytest.raises(GatewayError, match="Gateway error 500: Internal gateway failure"):
        list(client.stream_chat([{"role": "user", "content": "Hi"}]))
    client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_health() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "ok", "gateway": "runtime"}
    mock_resp.raise_for_status.return_value = None

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        client = GatewayClient()
        res = await client.health_async()
        assert res["status"] == "ok"
        client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_chat_completions() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"choices": [{"message": {"content": "Async response"}}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        client = GatewayClient()
        res = await client.chat_completions_async(
            [{"role": "user", "content": "Hi"}],
            tools=[{"type": "function", "function": {"name": "fn"}}],
        )
        assert res["choices"][0]["message"]["content"] == "Async response"
        client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_chat_completions_error() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Forbidden"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        client = GatewayClient()
        with pytest.raises(GatewayError, match="Gateway error 403: Forbidden"):
            await client.chat_completions_async([{"role": "user", "content": "Hi"}])
        client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_stream_chat() -> None:
    async def fake_aiter_lines() -> AsyncIterator[str]:
        yield "data: " + json.dumps({"choices": [{"delta": {"content": "Async Hello"}}]})
        yield "data: [DONE]"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = fake_aiter_lines

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
        client = GatewayClient()
        chunks = []
        async for chunk in client.stream_chat_async([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0]["choices"][0]["delta"]["content"] == "Async Hello"
        client.close()


def test_gateway_client_execute_tool_no_approval_token() -> None:
    mock_httpx = MagicMock()
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"status": "success"}
    mock_httpx.post.return_value = mock_resp

    client = GatewayClient(httpx_client=mock_httpx)
    client.execute_tool("read_file", {"path": "test.txt"})

    mock_httpx.post.assert_called_once_with(
        "/v1/tools/execute",
        json={"tool": "read_file", "arguments": {"path": "test.txt"}},
    )
    client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_stream_chat_error() -> None:
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.aread = AsyncMock(return_value=b"Async Gateway Crash")

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
        client = GatewayClient()
        with pytest.raises(GatewayError, match="Gateway error 500: Async Gateway Crash"):
            async for _ in client.stream_chat_async([{"role": "user", "content": "Hi"}]):
                pass
        client.close()


@pytest.mark.asyncio
async def test_gateway_client_async_stream_chat_malformed_lines() -> None:
    async def fake_aiter_lines() -> AsyncIterator[str]:
        yield ""
        yield "not data prefix"
        yield "data: {invalid json"
        yield "data: " + json.dumps({"choices": [{"delta": {"content": "Valid"}}]})
        yield "data: [DONE]"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.aiter_lines = fake_aiter_lines

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=None)

    with patch("httpx.AsyncClient.stream", return_value=mock_stream_ctx):
        client = GatewayClient()
        chunks = [
            chunk async for chunk in client.stream_chat_async([{"role": "user", "content": "Hi"}])
        ]
        assert len(chunks) == 1
        assert chunks[0]["choices"][0]["delta"]["content"] == "Valid"
        client.close()
