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

from ..agent.tools import Tool
from .client import DEFAULT_TIMEOUT, MCPClientError, StdioMCPClient
from .servers import MCPServerSpec, load_server_specs

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def connect_servers(
    specs: Sequence[MCPServerSpec] | None = None,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Iterator[list[Tool]]:
    """Start the given (or all configured) MCP servers and yield their tools.

    Passing ``specs=None`` loads them from ``load_server_specs()`` — so with no
    configured servers this yields ``[]`` and is a no-op.
    """
    if specs is None:
        specs = load_server_specs()
    clients: list[StdioMCPClient] = []
    tools: list[Tool] = []
    try:
        for spec in specs:
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
            tools.extend(client.as_tools(prefix=f"{spec.name}__"))
        yield tools
    finally:
        for client in clients:
            client.close()
