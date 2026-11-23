"""MCP stdio server (expose our tools) and client (use external servers')."""

from __future__ import annotations

from .client import MCPClientError, MCPToolError, RemoteMCPClient, StdioMCPClient
from .manager import connect_servers
from .server import handle_request, serve
from .servers import (
    GOOGLE_DEV_DOMAINS,
    PERSONA_DEFAULT_MCP_SERVERS,
    MCPServerSpec,
    format_google_dev_query,
    get_builtin_mcp_servers,
    load_server_specs,
    mcp_config_path,
    parse_mcp_servers,
)

__all__ = [
    "GOOGLE_DEV_DOMAINS",
    "MCPClientError",
    "MCPServerSpec",
    "MCPToolError",
    "PERSONA_DEFAULT_MCP_SERVERS",
    "RemoteMCPClient",
    "StdioMCPClient",
    "connect_servers",
    "format_google_dev_query",
    "get_builtin_mcp_servers",
    "handle_request",
    "load_server_specs",
    "mcp_config_path",
    "parse_mcp_servers",
    "serve",
]
