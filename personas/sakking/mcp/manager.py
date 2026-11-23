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
import os
import shutil
from collections.abc import Iterator, Sequence

from .. import config
from ..agent.security_hardening import MCPServerValidator, SecurityLevel
from ..agent.tools import Tool
from .client import MCPClientError, RemoteMCPClient, StdioMCPClient
from .servers import STREAMABLE_HTTP, MCPServerSpec, load_server_specs
from .client import (
    MCPClientError,
    RemoteMCPClient,
    StdioMCPClient,
    create_scoped_google_dev_tools,
)
from .servers import MCPServerSpec, load_server_specs

logger = logging.getLogger(__name__)

#: Transport values routed to :class:`RemoteMCPClient`. ``"sse"`` and ``"http"``
#: are legacy spellings that ``_parse_transport`` normalises away; they are
#: still accepted here for a spec constructed directly in code.
_REMOTE_TRANSPORTS = frozenset({STREAMABLE_HTTP, "sse", "http"})

_SECURITY_LEVELS = {
    "strict": SecurityLevel.STRICT,
    "balanced": SecurityLevel.BALANCED,
    "permissive": SecurityLevel.PERMISSIVE,
}


@contextlib.contextmanager
def connect_servers(
    specs: Sequence[MCPServerSpec] | None = None,
    *,
    timeout: float | None = None,
    include_builtins: bool = False,
    persona: str | None = None,
) -> Iterator[list[Tool]]:
    """Start the given (or all configured) MCP servers and yield their tools.

    Passing ``specs=None`` loads them from ``load_server_specs()`` — so with no
    configured servers this yields ``[]`` and is a no-op.
    """
    if specs is None:
        specs = load_server_specs(persona=persona, include_builtins=include_builtins)
    clients: list[StdioMCPClient | RemoteMCPClient] = []
    tools: list[Tool] = []
    # Was hardcoded BALANCED, which left STRICT — and with it the whole
    # approved-server allow-list — unreachable. See config.mcp_security_level().
    level = _SECURITY_LEVELS[config.mcp_security_level()]
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
                level,
            )
            if not is_valid:
                logger.warning("skipping unsafe MCP server %r: %s", spec.name, reason)
                continue

            client: StdioMCPClient | RemoteMCPClient
            if spec.transport in _REMOTE_TRANSPORTS or spec.url:
                if not spec.url:
                    logger.warning("skipping remote MCP server %r: missing url", spec.name)
                    continue
                remote_client = RemoteMCPClient(
                    spec.url,
                    name=spec.name,
                    headers=spec.headers,
                    timeout=timeout,
                )
                if not remote_client.is_configured():
                    logger.info(
                        "skipping remote MCP server %r: required authentication token is not set",
                        spec.name,
                    )
                    continue
                client = remote_client
            else:
                if not spec.command:
                    logger.warning("skipping MCP server %r: missing command", spec.name)
                    continue
                if spec.command in ("npx", "node", "npm") and shutil.which(spec.command) is None:
                    logger.info(
                        "skipping MCP server %r: %r binary not found in PATH",
                        spec.name,
                        spec.command,
                    )
                    continue
                if spec.name == "genkit" and not (
                    os.getenv("GENKIT_ENV")
                    or os.getenv("GENKIT_PROJECT_ID")
                    or os.getenv("FIREBASE_PROJECT_ID")
                    or os.getenv("SAKTHAI_ENABLE_GENKIT")
                ):
                    logger.info(
                        "skipping MCP server 'genkit': no Genkit environment configured (set SAKTHAI_ENABLE_GENKIT=1 or GENKIT_ENV)",
                    )
                    continue
                cmd = spec.command
                args = list(spec.args)
                is_sandboxed = spec.sandbox or os.environ.get(
                    "SAKTHAI_MCP_SANDBOX", ""
                ).strip().lower() in ("1", "true")
                if is_sandboxed and os.name == "posix":
                    # No lifetime cap: `timeout` is the per-request read budget,
                    # not how long the server may live. Passing it here wrapped
                    # the server in `timeout 30` and killed it thirty seconds
                    # after launch. Its lifetime is already bounded by
                    # `client.close()` in the `finally` below.
                    wrapped = MCPServerValidator.get_sandbox_wrapper(cmd, args=args)
                    cmd = wrapped[0]
                    args = wrapped[1:]
                client = StdioMCPClient(
                    cmd,
                    args,
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
            if spec.name == "google_dev_knowledge":
                with contextlib.suppress(Exception):
                    tools.extend(create_scoped_google_dev_tools(client, prefix=f"{spec.name}__"))
        yield tools
    finally:
        for client in clients:
            client.close()
