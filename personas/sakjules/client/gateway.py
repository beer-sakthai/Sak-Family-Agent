"""Native client SDK for the SakThai Runtime Gateway.

Provides synchronous and asynchronous clients with automatic discovery of gateway URL
and bearer token, SSE streaming, model and tool enumeration, and DataLossGuardrail execution.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx

logger = logging.getLogger("sakthai.client.gateway")

DEFAULT_GATEWAY_URL = "http://127.0.0.1:8080"


class GatewayError(RuntimeError):
    """Raised when an operation against the Runtime Gateway fails."""


class GatewayClient:
    """Client for communicating with the local or remote SakThai Runtime Gateway."""

    def __init__(
        self,
        base_url: str | None = None,
        api_token: str | None = None,
        *,
        timeout: float = 60.0,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (
            base_url
            or os.environ.get("SAKTHAI_GATEWAY_URL")
            or os.environ.get("NEXT_PUBLIC_GATEWAY_URL")
            or DEFAULT_GATEWAY_URL
        ).rstrip("/")
        self.api_token = (
            api_token
            or os.environ.get("SAKTHAI_GATEWAY_TOKEN")
            or os.environ.get("SAKTHAI_GATEWAY_API_KEY")
            or os.environ.get("SAKTHAI_GATEWAY_BEARER_TOKEN")
            or os.environ.get("SAKTHAI_API_TOKEN")
        )
        self.timeout = timeout
        self._headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_token:
            self._headers["Authorization"] = f"Bearer {self.api_token.strip()}"

        self._client = httpx_client or httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=self.timeout,
        )

    @property
    def headers(self) -> dict[str, str]:
        """Headers used for requests."""
        return dict(self._headers)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> GatewayClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """Forward GET request to the underlying client."""
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        """Forward POST request to the underlying client."""
        return self._client.post(path, **kwargs)

    def stream(self, method: str, path: str, **kwargs: Any) -> Any:
        """Forward stream request to the underlying client."""
        return self._client.stream(method, path, **kwargs)

    def health(self) -> dict[str, Any]:
        """Check gateway health and status."""
        resp = self.get("/health")
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def list_models(self) -> list[dict[str, Any]]:
        """List models available on the gateway."""
        resp = self.get("/v1/models")
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])  # type: ignore[no-any-return]

    def list_personas(self) -> list[dict[str, Any]]:
        """List active persona configurations."""
        resp = self.get("/v1/personas")
        resp.raise_for_status()
        data = resp.json()
        return data.get("personas", [])  # type: ignore[no-any-return]

    def list_tools(self) -> list[dict[str, Any]]:
        """List tools registered on the gateway."""
        resp = self.get("/v1/tools")
        resp.raise_for_status()
        data = resp.json()
        return data.get("tools", [])  # type: ignore[no-any-return]

    def execute_tool(
        self,
        tool: str,
        arguments: dict[str, Any] | None = None,
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        """Execute a tool with DataLossGuardrail enforcement."""
        payload: dict[str, Any] = {"tool": tool, "arguments": arguments or {}}
        if approval_token:
            payload["approval_token"] = approval_token
        resp = self.post("/v1/tools/execute", json=payload)
        return resp.json()  # type: ignore[no-any-return]

    def chat_completions(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "sakthai",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate non-streaming chat completions."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        resp = self.post("/v1/chat/completions", json=payload)
        if resp.status_code >= 400:
            raise GatewayError(f"Gateway error {resp.status_code}: {resp.text}")
        return resp.json()  # type: ignore[no-any-return]

    def stream_chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "sakthai",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Iterator[dict[str, Any]]:
        """Stream chat completion chunks via Server-Sent Events (SSE)."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        with self.stream("POST", "/v1/chat/completions", json=payload) as response:
            if response.status_code >= 400:
                content = response.read().decode("utf-8", errors="replace")
                raise GatewayError(f"Gateway error {response.status_code}: {content}")
            for line in response.iter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:") :].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    yield chunk
                except json.JSONDecodeError:
                    continue

    async def health_async(self) -> dict[str, Any]:
        """Asynchronously check gateway health."""
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self._headers, timeout=self.timeout
        ) as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def chat_completions_async(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "sakthai",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Asynchronously generate non-streaming chat completions."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self._headers, timeout=self.timeout
        ) as client:
            resp = await client.post("/v1/chat/completions", json=payload)
            if resp.status_code >= 400:
                raise GatewayError(f"Gateway error {resp.status_code}: {resp.text}")
            return resp.json()  # type: ignore[no-any-return]

    async def stream_chat_async(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str = "sakthai",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[dict[str, Any]]:
        """Asynchronously stream chat completion chunks via SSE."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with (
            httpx.AsyncClient(
                base_url=self.base_url, headers=self._headers, timeout=self.timeout
            ) as client,
            client.stream("POST", "/v1/chat/completions", json=payload) as response,
        ):
            if response.status_code >= 400:
                content = (await response.aread()).decode("utf-8", errors="replace")
                raise GatewayError(f"Gateway error {response.status_code}: {content}")
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:") :].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    yield chunk
                except json.JSONDecodeError:
                    continue
