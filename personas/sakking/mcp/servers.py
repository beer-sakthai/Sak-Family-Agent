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
from collections.abc import Callable
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


GOOGLE_DEV_DOMAINS: tuple[str, ...] = (
    "developer.chrome.com",
    "web.dev",
    "developers.google.com",
    "antigravity.google",
    "adk.dev",
)

PERSONA_DEFAULT_MCP_SERVERS: dict[str, tuple[str, ...]] = {
    "sakthai": ("huggingface",),
    "saksee": ("figma", "google_dev_knowledge"),
    "sakjules": ("genkit", "google_dev_knowledge"),
    "sakking": ("genkit", "google_dev_knowledge"),
    "saksit": ("huggingface", "figma"),
    "saktan": ("genkit",),
}


def builtin_genkit_server() -> MCPServerSpec:
    """Built-in Firebase Genkit MCP server using stdio."""
    return MCPServerSpec(
        name="genkit",
        command="npx",
        args=["-y", "genkit", "mcp"],
        transport="stdio",
    )


def builtin_google_dev_knowledge_server(api_key: str | None = None) -> MCPServerSpec:
    """Built-in Google Developer Knowledge remote MCP server with domain scoping."""
    key = api_key or os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    headers = {"x-goog-api-key": key} if key else {}
    return MCPServerSpec(
        name="google_dev_knowledge",
        url="https://developerknowledge.googleapis.com/mcp",
        transport="sse",
        headers=headers,
    )


def builtin_figma_server(token: str | None = None) -> MCPServerSpec:
    """Built-in Figma remote MCP server."""
    tok = token or os.getenv("FIGMA_ACCESS_TOKEN", "") or os.getenv("FIGMA_TOKEN", "")
    headers = (
        {
            "Authorization": f"Bearer {tok}",
            "X-Figma-Token": tok,
        }
        if tok
        else {}
    )
    return MCPServerSpec(
        name="figma",
        url="https://mcp.figma.com/mcp",
        transport="sse",
        headers=headers,
    )


def builtin_huggingface_server(token: str | None = None) -> MCPServerSpec:
    """Built-in Hugging Face remote MCP server."""
    tok = token or os.getenv("HF_TOKEN", "")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    return MCPServerSpec(
        name="huggingface",
        url="https://huggingface.co/mcp?login&gradio=none",
        transport="sse",
        headers=headers,
    )


BUILTIN_SERVER_FACTORIES: dict[str, Callable[[], MCPServerSpec]] = {
    "genkit": builtin_genkit_server,
    "google_dev_knowledge": builtin_google_dev_knowledge_server,
    "figma": builtin_figma_server,
    "huggingface": builtin_huggingface_server,
}


def get_builtin_mcp_servers(persona: str | None = None) -> list[MCPServerSpec]:
    """Retrieve built-in MCP server specifications, optionally filtered by persona loadout."""
    if persona and persona.lower() in PERSONA_DEFAULT_MCP_SERVERS:
        selected_names = PERSONA_DEFAULT_MCP_SERVERS[persona.lower()]
        return [
            BUILTIN_SERVER_FACTORIES[name]()
            for name in selected_names
            if name in BUILTIN_SERVER_FACTORIES
        ]
    return [factory() for factory in BUILTIN_SERVER_FACTORIES.values()]


def format_google_dev_query(query: str, domain: str | None = None) -> str:
    """Format or scope a developer knowledge query to one of the approved domains."""
    if not domain:
        return query
    clean_domain = domain.strip().lower()
    if clean_domain not in GOOGLE_DEV_DOMAINS:
        logger.warning(
            "domain %r is not in approved GOOGLE_DEV_DOMAINS %s; formatting anyway",
            domain,
            GOOGLE_DEV_DOMAINS,
        )
    return f"site:{clean_domain} {query}".strip()


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


def load_server_specs(
    persona: str | None = None,
    *,
    include_builtins: bool = False,
) -> list[MCPServerSpec]:
    """All configured MCP servers, lowest precedence first.

    Sources, each overriding the previous by server name: built-in servers
    (if requested or SAKTHAI_ENABLE_BUILTIN_MCP=1) → gemini extensions →
    sakthai extensions → persona extensions → ``~/.sakthai/mcp.json`` → the per-persona override from
    ``SAKTHAI_MCP_CONFIG`` (highest). So a persona's ``mcp.json`` wins over the
    shared config, which wins over an extension of the same name.
    """
    by_name: dict[str, MCPServerSpec] = {}

    # 0. Built-in servers (lowest precedence, opt-in or env gated)
    if include_builtins or os.environ.get("SAKTHAI_ENABLE_BUILTIN_MCP", "").strip().lower() in (
        "1",
        "true",
    ):
        active_persona = persona or os.environ.get("SAKTHAI_PERSONA")
        for spec in get_builtin_mcp_servers(active_persona):
            by_name[spec.name] = spec

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
