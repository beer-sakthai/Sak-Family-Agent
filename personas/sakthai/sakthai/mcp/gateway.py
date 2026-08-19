"""Unified Model Context Protocol (MCP) Tool Gateway & Federation Router."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from .models import MCPServerRegistration, MCPToolDefinition, TransportType
from .security import validate_tool_arguments

logger = logging.getLogger(__name__)


class MCPGateway:
    """Aggregates multiple MCP servers, namespaces tool calls, and secures execution."""

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerRegistration] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Awaitable[Any]]] = {}

    def register_server(
        self,
        server_id: str,
        transport: TransportType,
        endpoint: str | None = None,
    ) -> MCPServerRegistration:
        server = MCPServerRegistration(server_id=server_id, transport=transport, endpoint=endpoint)
        self._servers[server_id] = server
        return server

    def register_tool(
        self,
        server_id: str,
        transport: TransportType,
        tool: MCPToolDefinition,
        handler: Callable[[dict[str, Any]], Awaitable[Any]],
    ) -> str:
        if server_id not in self._servers:
            self.register_server(server_id, transport)

        server = self._servers[server_id]
        server.tools.append(tool)

        qualified_name = f"{server_id}::{tool.name}"
        self._handlers[qualified_name] = handler
        return qualified_name

    def list_tools(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for server in self._servers.values():
            for tool in server.tools:
                results.append(
                    {
                        "qualified_name": f"{server.server_id}::{tool.name}",
                        "server_id": server.server_id,
                        "transport": server.transport.value,
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    }
                )
        return results

    async def invoke_tool(self, qualified_name: str, arguments: dict[str, Any]) -> Any:
        if qualified_name not in self._handlers:
            raise KeyError(f"Tool {qualified_name} not found in MCP Gateway.")

        # Zero-tolerance security validation
        validated_args = validate_tool_arguments(arguments)

        handler = self._handlers[qualified_name]
        return await handler(validated_args)
