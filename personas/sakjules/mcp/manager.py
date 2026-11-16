"""Connect to configured MCP servers and expose their tools to the agent.

:func:`connect_servers` is a context manager: it starts each server (failing
soft — a server that won't start is logged and skipped), yields the merged list
of their tools (namespaced ``<server>__<tool>`` so they can't clash with the
built-ins or each other), and closes every client on exit. Run the agent loop
*inside* the ``with`` so the subprocesses stay alive while their tools are called:

    with connect_servers() as mcp_tools:
        run_agent(task, tools=(*BUILTIN_TOOLS, *mcp_tools))
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Iterator, Sequence

from ..agent.security_hardening import MCPServerValidator, SecurityLevel
from ..agent.tools import Tool
from .client import MCPClientError, RemoteMCPClient, StdioMCPClient
from .servers import MCPServerSpec, load_server_specs

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def connect_servers(
    specs: Sequence[MCPServerSpec] | None = None,
    *,
    timeout: float | None = None,
) -> Iterator[list[Tool]]:
    """Start the given (or all configured) MCP servers and yield their tools.

    Passing ``specs=None`` loads them from ``load_server_specs()`` — so with no
    configured servers this yields ``[]`` and is a no-op.
    """
    if specs is None:
        specs = load_server_specs()
    clients: list[StdioMCPClient | RemoteMCPClient] = []
    tools: list[Tool] = []
    try:
        for spec in specs:
            is_valid, reason = MCPServerValidator.validate_server_config(
                {
                    "name": spec.name,
                    "command": spec.command or "",
                    "args": spec.args,
                    "env": spec.env,
                    "cwd": spec.cwd,
                    "url": spec.url or "",
                },
                SecurityLevel.BALANCED,
            )
            if not is_valid:
                logger.warning("skipping unsafe MCP server %r: %s", spec.name, reason)
                continue

            client: StdioMCPClient | RemoteMCPClient
            if spec.transport in ("sse", "http") or spec.url:
                if not spec.url:
                    logger.warning("skipping remote MCP server %r: missing url", spec.name)
                    continue
                client = RemoteMCPClient(
                    spec.url,
                    name=spec.name,
                    timeout=timeout,
                )
            else:
                if not spec.command:
                    logger.warning("skipping MCP server %r: missing command", spec.name)
                    continue
                client = StdioMCPClient(
                    spec.command,
                    spec.args,
                    env=spec.env or None,
                    cwd=spec.cwd,
                    name=spec.name,
                    timeout=timeout,
                )

            try:
                client.start()
            except MCPClientError as exc:
                logger.warning("skipping MCP server %r: %s", spec.name, exc)
                client.close()
                continue
            clients.append(client)
            if spec.tools is not None:
                tools.extend(client.as_tools(prefix=f"{spec.name}__", allowed_tools=spec.tools))
            else:
                tools.extend(client.as_tools(prefix=f"{spec.name}__"))
        yield tools
    finally:
        for client in clients:
            client.close()
