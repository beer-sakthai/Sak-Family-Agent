"""Python client for Microsoft Work IQ MCP remote endpoints."""

from __future__ import annotations

from typing import Any

import httpx

ALLOWED_READ_TOOLS = frozenset({"retrieve", "search", "query", "list", "summarize", "find"})
DISALLOWED_MUTATING_KEYWORDS = (
    "create",
    "delete",
    "update",
    "send",
    "write",
    "modify",
    "remove",
    "post",
)


class WorkIQSecurityError(Exception):
    """Raised when an unapproved or mutating Work IQ tool is requested."""


class WorkIQClient:
    """Client for connecting to Microsoft Work IQ MCP server over Streamable HTTP."""

    def __init__(
        self,
        endpoint: str = "https://api.workiq.microsoft.com/mcp",
        user_bearer_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.endpoint = endpoint
        self.user_bearer_token = user_bearer_token
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.user_bearer_token:
            headers["Authorization"] = f"Bearer {self.user_bearer_token}"
        return headers

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Verify tool is strictly read-only and contained in allow-list."""
        normalized = tool_name.strip().lower()
        if any(keyword in normalized for keyword in DISALLOWED_MUTATING_KEYWORDS):
            return False
        return normalized in ALLOWED_READ_TOOLS

    def filter_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter remote tools to retain only read-only safe tools."""
        safe_tools = []
        for tool in tools:
            name = tool.get("name", "")
            if self.is_tool_allowed(name):
                safe_tools.append(tool)
        return safe_tools

    async def retrieve(self, query: str, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
        """Execute read-only 'retrieve' call against Work IQ endpoint."""
        if not self.is_tool_allowed("retrieve"):
            raise WorkIQSecurityError("Tool 'retrieve' is not permitted by policy.")

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "retrieve",
                "arguments": {"query": query},
            },
        }

        should_close = False
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)
            should_close = True

        try:
            resp = await client.post(self.endpoint, headers=self._get_headers(), json=payload)
            resp.raise_for_status()
            return resp.json()
        finally:
            if should_close:
                await client.aclose()
