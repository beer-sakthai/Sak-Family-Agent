"""Discover external MCP servers to connect to.

Reads the standard ``mcpServers`` manifest shape (``command`` / ``args`` /
``env``) used by Claude Desktop and gemini-extension.json. Specs come from
``~/.sakthai/mcp.json`` (the primary config) and from each installed extension's
``gemini-extension.json``. Only stdio ``command`` servers are supported; on a
name clash ``mcp.json`` wins over an extension.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import gemini_extensions_dir, mcp_config_override, sakthai_home
from ..extensions.install import extensions_dir

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

    raw_type = entry.get("type") or entry.get("transport")
    if isinstance(raw_type, str):
        t_lower = raw_type.lower()
        if t_lower in ("local", "stdio"):
            transport = "stdio"
        elif t_lower in ("sse", "http"):
            transport = "sse"
        else:
            transport = t_lower
    else:
        transport = "sse" if url and not command else "stdio"

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


def load_server_specs() -> list[MCPServerSpec]:
    """All configured MCP servers, lowest precedence first.

    Sources, each overriding the previous by server name: gemini extensions →
    sakthai extensions → ``~/.sakthai/mcp.json`` → the per-persona override from
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

    # 2. Load from sakthai extensions
    base = extensions_dir()
    if base.is_dir():
        for manifest in sorted(base.glob("*/gemini-extension.json")):
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
