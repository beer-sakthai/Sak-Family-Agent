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
from dataclasses import dataclass, field
from pathlib import Path

from ..config import sakthai_home
from ..extensions.install import extensions_dir

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MCPServerSpec:
    """How to launch one external MCP server over stdio."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None


def mcp_config_path() -> Path:
    """The primary config file listing external MCP servers to auto-load."""
    return sakthai_home() / "mcp.json"


def parse_mcp_servers(data: object) -> list[MCPServerSpec]:
    """Parse the ``mcpServers`` object of a manifest into specs.

    Tolerant of junk: invalid or non-``command`` entries are skipped, not raised.
    """
    if not isinstance(data, dict):
        return []
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        return []
    specs: list[MCPServerSpec] = []
    for name, entry in servers.items():
        if not isinstance(name, str) or not isinstance(entry, dict):
            continue
        command = entry.get("command")
        if not isinstance(command, str) or not command:
            continue  # only stdio "command" servers are supported
        raw_args = entry.get("args")
        args = [str(a) for a in raw_args] if isinstance(raw_args, list) else []
        raw_env = entry.get("env")
        env = {str(k): str(v) for k, v in raw_env.items()} if isinstance(raw_env, dict) else {}
        raw_cwd = entry.get("cwd")
        cwd = raw_cwd if isinstance(raw_cwd, str) else None
        specs.append(MCPServerSpec(name=name, command=command, args=args, env=env, cwd=cwd))
    return specs


def _load_manifest(path: Path) -> list[MCPServerSpec]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("could not read MCP manifest %s: %s", path, exc)
        return []
    return parse_mcp_servers(data)


def load_server_specs() -> list[MCPServerSpec]:
    """All configured MCP servers: installed extensions first, then mcp.json.

    Later sources override earlier ones by name, so ``~/.sakthai/mcp.json`` wins
    over an extension that declares a server of the same name.
    """
    by_name: dict[str, MCPServerSpec] = {}
    base = extensions_dir()
    if base.is_dir():
        for manifest in sorted(base.glob("*/gemini-extension.json")):
            for spec in _load_manifest(manifest):
                by_name[spec.name] = spec
    config = mcp_config_path()
    if config.is_file():
        for spec in _load_manifest(config):
            by_name[spec.name] = spec
    return list(by_name.values())
