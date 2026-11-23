"""Discover external MCP servers to connect to.

Reads the standard ``mcpServers`` manifest shape (``command`` / ``args`` /
``env``) used by Claude Desktop and gemini-extension.json. Specs come from
``~/.sakthai/mcp.json`` (the primary config) and from each installed extension's
``gemini-extension.json``. Both locally spawned stdio servers (``command``) and
remote Streamable HTTP servers (``url``) are supported; on a name clash
``mcp.json`` wins over an extension.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import (
    PERSONA_NAMES,
    gemini_extensions_dir,
    mcp_config_override,
    persona_extensions_dir,
    sakthai_home,
)
from ..extensions.install import extensions_dir
from .lifecycle import warn_deprecated

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MCPServerSpec:
    """How to connect to or launch one external MCP server."""

    name: str
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    url: str | None = None
    transport: str = "stdio"
    tools: list[str] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    sandbox: bool = False


def mcp_config_path() -> Path:
    """The primary config file listing external MCP servers to auto-load."""
    return sakthai_home() / "mcp.json"


#: The transport name for a remote server reached over HTTP POST.
#:
#: ``"sse"`` is the deprecated alias. It never described what the client does:
#: ``RemoteMCPClient`` POSTs JSON-RPC and accepts either a JSON or an SSE-framed
#: reply, which is Streamable HTTP; there is no GET stream, and a GET stream is
#: what an SSE transport would be. See ``mcp/lifecycle.py``.
STREAMABLE_HTTP = "streamable-http"

#: Accepted spellings for the remote transport, mapped to :data:`STREAMABLE_HTTP`.
_REMOTE_TRANSPORT_ALIASES = {"streamable-http", "streamable_http", "http", "sse"}

#: Accepted spellings for a locally spawned stdio server.
_STDIO_TRANSPORT_ALIASES = {"stdio", "local"}


def _parse_transport(raw_type: object, name: str, url: str | None, command: str | None) -> str:
    """The transport for one manifest entry, normalising legacy spellings.

    With no ``type``/``transport`` key the transport is inferred, as before,
    from whether the entry carries a ``url`` or a ``command`` — which is how
    every remote server in the six shipped persona manifests is configured, so
    this path is the common one and must not warn.
    """
    if not isinstance(raw_type, str):
        return STREAMABLE_HTTP if url and not command else "stdio"

    lowered = raw_type.strip().lower()
    if lowered in _STDIO_TRANSPORT_ALIASES:
        return "stdio"
    if lowered in _REMOTE_TRANSPORT_ALIASES:
        if lowered == "sse":
            warn_deprecated('transport: "sse"', context=f"MCP server {name!r}")
        return STREAMABLE_HTTP
    # Unknown values pass through lowercased, as before: the manager decides
    # what to do with them, and rejecting here would be a behaviour change.
    return lowered


def _parse_server_entry(name: str, entry: dict[str, Any]) -> MCPServerSpec | None:
    if not isinstance(entry, dict):
        return None
    raw_command = entry.get("command")
    command = str(raw_command) if isinstance(raw_command, str) and raw_command else None

    raw_url = entry.get("url")
    url = str(raw_url) if isinstance(raw_url, str) and raw_url else None

    if not command and not url:
        return None

    raw_args = entry.get("args")
    args = [str(a) for a in raw_args] if isinstance(raw_args, list) else []

    raw_env = entry.get("env")
    env = {str(k): str(v) for k, v in raw_env.items()} if isinstance(raw_env, dict) else {}

    raw_cwd = entry.get("cwd")
    cwd = raw_cwd if isinstance(raw_cwd, str) else None

    raw_tools = entry.get("tools")
    tools = [str(t) for t in raw_tools] if isinstance(raw_tools, list) else None

    raw_headers = entry.get("headers")
    headers = (
        {str(k): os.path.expandvars(str(v)) for k, v in raw_headers.items()}
        if isinstance(raw_headers, dict)
        else {}
    )

    raw_sandbox = entry.get("sandbox")
    sandbox = bool(raw_sandbox) if raw_sandbox is not None else False

    transport = _parse_transport(entry.get("type") or entry.get("transport"), name, url, command)

    return MCPServerSpec(
        name=name,
        command=command,
        args=args,
        env=env,
        cwd=cwd,
        url=url,
        transport=transport,
        tools=tools,
        headers=headers,
        sandbox=sandbox,
    )


def parse_mcp_servers(data: object) -> list[MCPServerSpec]:
    """Parse the ``mcpServers`` or ``servers`` object of a manifest into specs.

    Tolerant of junk: invalid or missing entries are skipped, not raised.
    """
    if not isinstance(data, dict):
        return []
    specs: list[MCPServerSpec] = []

    # 1. Standard mcpServers mapping (Claude Desktop / Gemini format)
    servers = data.get("mcpServers")
    if isinstance(servers, dict):
        for name, entry in servers.items():
            if isinstance(name, str) and isinstance(entry, dict):
                spec = _parse_server_entry(name, entry)
                if spec is not None:
                    specs.append(spec)

    # 2. List or dict format (e.g. docs/example-mcp.json)
    list_servers = data.get("servers")
    if isinstance(list_servers, list):
        for entry in list_servers:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                spec = _parse_server_entry(entry["name"], entry)
                if spec is not None:
                    specs.append(spec)
    elif isinstance(list_servers, dict):
        for name, entry in list_servers.items():
            if isinstance(name, str) and isinstance(entry, dict):
                spec = _parse_server_entry(name, entry)
                if spec is not None:
                    specs.append(spec)

    return specs


def _load_manifest(path: Path) -> list[MCPServerSpec]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("could not read MCP manifest %s: %s", path, exc)
        return []
    return parse_mcp_servers(data)


def load_server_specs(persona: str | None = None) -> list[MCPServerSpec]:
    """All configured MCP servers, lowest precedence first.

    Sources, each overriding the previous by server name: gemini extensions →
    sakthai extensions → persona extensions → ``~/.sakthai/mcp.json`` → the per-persona override from
    ``SAKTHAI_MCP_CONFIG`` (highest). So a persona's ``mcp.json`` wins over the
    shared config, which wins over an extension of the same name.
    """
    by_name: dict[str, MCPServerSpec] = {}

    # 1. Load from gemini extensions
    gemini_base = gemini_extensions_dir()
    if gemini_base.is_dir():
        for manifest in sorted(gemini_base.glob("*/gemini-extension.json")):
            for spec in _load_manifest(manifest):
                by_name[spec.name] = spec

    # 2. Load from shared sakthai extensions
    base = extensions_dir()
    if base.is_dir():
        for manifest in sorted(base.glob("*/gemini-extension.json")):
            for spec in _load_manifest(manifest):
                by_name[spec.name] = spec

    # 2b. Load from persona extensions (if persona provided or detected)
    active_persona = persona or os.environ.get("SAKTHAI_PERSONA")
    if active_persona and active_persona in PERSONA_NAMES:
        p_base = persona_extensions_dir(active_persona)
        if p_base.is_dir():
            for manifest in sorted(p_base.glob("*/gemini-extension.json")):
                for spec in _load_manifest(manifest):
                    by_name[spec.name] = spec

    # 3. Shared primary config
    config = mcp_config_path()
    if config.is_file():
        for spec in _load_manifest(config):
            by_name[spec.name] = spec

    # 4. Per-persona override (SAKTHAI_MCP_CONFIG) — highest precedence
    persona_config = mcp_config_override()
    if persona_config is not None and persona_config.is_file():
        for spec in _load_manifest(persona_config):
            by_name[spec.name] = spec

    return list(by_name.values())
