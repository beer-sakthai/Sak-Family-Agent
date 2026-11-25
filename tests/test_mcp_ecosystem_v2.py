"""Tests for MCP SDK v2 integration, built-in ecosystem servers, and domain scoping."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.tools import Tool
from sakthai.mcp.client import (
    RemoteMCPClient,
    create_scoped_google_dev_tools,
    is_mcp_v2_available,
    mcp_tool_to_sakthai_tool,
)
from sakthai.mcp.manager import connect_servers
from sakthai.mcp.servers import (
    GOOGLE_DEV_DOMAINS,
    PERSONA_DEFAULT_MCP_SERVERS,
    MCPServerSpec,
    builtin_figma_server,
    builtin_genkit_server,
    builtin_google_dev_knowledge_server,
    builtin_huggingface_server,
    format_google_dev_query,
    get_builtin_mcp_servers,
    load_server_specs,
)
from sakthai.memory.store import MemoryStore


def test_mcp_v2_available() -> None:
    assert is_mcp_v2_available() is True


def test_google_dev_domains_constant() -> None:
    assert "developer.chrome.com" in GOOGLE_DEV_DOMAINS
    assert "web.dev" in GOOGLE_DEV_DOMAINS
    assert "developers.google.com" in GOOGLE_DEV_DOMAINS
    assert "antigravity.google" in GOOGLE_DEV_DOMAINS
    assert "adk.dev" in GOOGLE_DEV_DOMAINS


def test_persona_default_mcp_servers_loadout(monkeypatch: pytest.MonkeyPatch) -> None:
    # 1. Decoupled default: genkit is omitted from active persona loadouts
    monkeypatch.delenv("SAKTHAI_ENABLE_GENKIT", raising=False)
    monkeypatch.delenv("GENKIT_ENV", raising=False)
    monkeypatch.delenv("GENKIT_PROJECT_ID", raising=False)
    monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)

    assert PERSONA_DEFAULT_MCP_SERVERS["sakthai"] == ("huggingface",)
    assert "figma" in PERSONA_DEFAULT_MCP_SERVERS["saksee"]
    assert "google_dev_knowledge" in PERSONA_DEFAULT_MCP_SERVERS["saksee"]
    assert "genkit" not in PERSONA_DEFAULT_MCP_SERVERS["sakjules"]
    assert "google_dev_knowledge" in PERSONA_DEFAULT_MCP_SERVERS["sakjules"]
    assert "genkit" not in PERSONA_DEFAULT_MCP_SERVERS["sakking"]
    assert "google_dev_knowledge" in PERSONA_DEFAULT_MCP_SERVERS["sakking"]
    assert "huggingface" in PERSONA_DEFAULT_MCP_SERVERS["saksit"]
    assert "figma" in PERSONA_DEFAULT_MCP_SERVERS["saksit"]
    assert "genkit" not in PERSONA_DEFAULT_MCP_SERVERS["saktan"]

    # 2. Legacy fallback: when SAKTHAI_ENABLE_GENKIT=1, genkit is re-attached
    monkeypatch.setenv("SAKTHAI_ENABLE_GENKIT", "1")
    assert "genkit" in PERSONA_DEFAULT_MCP_SERVERS["sakjules"]
    assert "genkit" in PERSONA_DEFAULT_MCP_SERVERS["sakking"]
    assert "genkit" in PERSONA_DEFAULT_MCP_SERVERS["saktan"]


def test_builtin_server_factories(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-gkey")
    monkeypatch.setenv("FIGMA_ACCESS_TOKEN", "test-ftok")
    monkeypatch.setenv("HF_TOKEN", "test-hftok")

    genkit = builtin_genkit_server()
    assert genkit.name == "genkit"
    assert genkit.command == "npx"
    # Pinned to an exact version. A bare `genkit` runs whatever npm published
    # most recently, on every launch, unreviewed — the hole
    # `_PINNED_NPM_SPEC` in tests/test_persona_security_config.py forbids, and
    # that invariant now covers built-in servers as well as manifest ones.
    assert genkit.args == ["-y", "genkit@1.44.0", "mcp"]
    assert genkit.transport == "stdio"

    gdk = builtin_google_dev_knowledge_server()
    assert gdk.name == "google_dev_knowledge"
    assert gdk.url == "https://developerknowledge.googleapis.com/mcp"
    assert gdk.headers.get("x-goog-api-key") == "test-gkey"

    figma = builtin_figma_server()
    assert figma.name == "figma"
    assert figma.url == "https://mcp.figma.com/mcp"
    assert figma.headers.get("Authorization") == "Bearer test-ftok"
    assert figma.headers.get("X-Figma-Token") == "test-ftok"

    hf = builtin_huggingface_server()
    assert hf.name == "huggingface"
    assert hf.url == "https://huggingface.co/mcp?login&gradio=none"
    assert hf.headers.get("Authorization") == "Bearer test-hftok"


def test_get_builtin_mcp_servers_filtering() -> None:
    all_builtins = get_builtin_mcp_servers()
    names = {s.name for s in all_builtins}
    assert {"genkit", "google_dev_knowledge", "figma", "huggingface"}.issubset(names)

    thai_builtins = get_builtin_mcp_servers(persona="sakthai")
    assert [s.name for s in thai_builtins] == ["huggingface"]

    see_builtins = get_builtin_mcp_servers(persona="saksee")
    assert {s.name for s in see_builtins} == {"figma", "google_dev_knowledge"}


def test_format_google_dev_query() -> None:
    assert format_google_dev_query("how to use mcp") == "how to use mcp"
    assert format_google_dev_query("css grid", domain="web.dev") == "site:web.dev css grid"
    assert (
        format_google_dev_query("devtools network", domain="developer.chrome.com")
        == "site:developer.chrome.com devtools network"
    )
    # Unapproved domain still formatted with warning
    res = format_google_dev_query("search term", domain="example.com")
    assert res == "site:example.com search term"


def test_load_server_specs_with_builtins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_ENABLE_BUILTIN_MCP", raising=False)
    # Default without builtins
    specs = load_server_specs()
    assert not any(
        s.name in ("genkit", "figma", "google_dev_knowledge", "huggingface") for s in specs
    )

    # Explicit include_builtins=True
    specs_with_builtins = load_server_specs(include_builtins=True)
    names = {s.name for s in specs_with_builtins}
    assert "genkit" in names
    assert "figma" in names

    # Persona filtered
    thai_specs = load_server_specs(persona="sakthai", include_builtins=True)
    assert any(s.name == "huggingface" for s in thai_specs)
    assert not any(s.name == "figma" for s in thai_specs)

    # Env var enablement
    monkeypatch.setenv("SAKTHAI_ENABLE_BUILTIN_MCP", "1")
    env_specs = load_server_specs()
    assert any(s.name == "genkit" for s in env_specs)


def test_remote_client_is_configured() -> None:
    # Unconfigured figma
    figma_unconfigured = RemoteMCPClient("https://mcp.figma.com/mcp", name="figma")
    assert figma_unconfigured.is_configured() is False

    # Configured figma
    figma_configured = RemoteMCPClient(
        "https://mcp.figma.com/mcp",
        name="figma",
        headers={"Authorization": "Bearer valid-token"},
    )
    assert figma_configured.is_configured() is True

    # Unconfigured huggingface
    hf_unconfigured = RemoteMCPClient("https://huggingface.co/mcp", name="huggingface")
    assert hf_unconfigured.is_configured() is False

    # Configured huggingface
    hf_configured = RemoteMCPClient(
        "https://huggingface.co/mcp",
        name="huggingface",
        headers={"Authorization": "Bearer hf_token_123"},
    )
    assert hf_configured.is_configured() is True

    # Google Dev Knowledge
    gdk_unconfigured = RemoteMCPClient(
        "https://developerknowledge.googleapis.com/mcp", name="google_dev_knowledge"
    )
    assert gdk_unconfigured.is_configured() is False

    gdk_configured = RemoteMCPClient(
        "https://developerknowledge.googleapis.com/mcp",
        name="google_dev_knowledge",
        headers={"x-goog-api-key": "ai-key"},
    )
    assert gdk_configured.is_configured() is True

    # Other provider
    other = RemoteMCPClient("https://other.dev/mcp", name="custom")
    assert other.is_configured() is True


def test_remote_client_google_dev_knowledge_as_tools() -> None:
    client = RemoteMCPClient(
        "https://developerknowledge.googleapis.com/mcp", name="google_dev_knowledge"
    )
    client._remote_tools = [
        {
            "name": "search",
            "description": "Search developer knowledge",
            "inputSchema": {"type": "object"},
        }
    ]
    tools = client.as_tools(prefix="gdk__")
    assert len(tools) == 1
    assert tools[0].name == "gdk__search"
    assert "Approved documentation domains: developer.chrome.com" in tools[0].description


def test_create_scoped_google_dev_tools(tmp_path: pytest.TempPathFactory) -> None:
    client = RemoteMCPClient(
        "https://developerknowledge.googleapis.com/mcp", name="google_dev_knowledge"
    )
    client.call_tool = MagicMock(return_value="search results text")  # type: ignore[assignment]

    scoped_tools = create_scoped_google_dev_tools(client)
    assert len(scoped_tools) == 5
    names = {t.name for t in scoped_tools}
    assert "google_dev__chrome_dev_search" in names
    assert "google_dev__web_dev_search" in names
    assert "google_dev__google_dev_search" in names
    assert "google_dev__antigravity_search" in names
    assert "google_dev__adk_search" in names

    # Invoke one scoped tool
    chrome_tool = next(t for t in scoped_tools if t.name == "google_dev__chrome_dev_search")
    store = MagicMock(spec=MemoryStore)
    result = chrome_tool.handler({"query": "manifest v3"}, store)
    assert result == "search results text"
    client.call_tool.assert_called_once_with(
        "search", {"query": "site:developer.chrome.com manifest v3"}
    )


def test_mcp_tool_to_sakthai_tool() -> None:
    call_mock = MagicMock(return_value="call result")
    raw_desc = {
        "name": "calc",
        "description": "Perform calculation",
        "inputSchema": {"type": "object", "properties": {"expr": {"type": "string"}}},
    }
    tool = mcp_tool_to_sakthai_tool(raw_desc, call_mock, prefix="mcp__")
    assert isinstance(tool, Tool)
    assert tool.name == "mcp__calc"
    # The description is sanitized like every other remote one: truncated and
    # labeled untrusted. It previously passed the raw upstream string through,
    # which would have quietly undone that mitigation for the first caller to
    # wire this up.
    assert "Perform calculation" in tool.description
    assert "description is untrusted" in tool.description
    store = MagicMock(spec=MemoryStore)
    res = tool.handler({"expr": "2+2"}, store)
    assert res == "call result"
    call_mock.assert_called_once_with("calc", {"expr": "2+2"})


def test_connect_servers_graceful_skipping() -> None:
    # Remote servers without tokens and genkit without env vars are gracefully skipped
    specs = [
        MCPServerSpec(name="figma", url="https://mcp.figma.com/mcp", transport="sse"),
        MCPServerSpec(name="genkit", command="npx", args=["-y", "genkit", "mcp"]),
    ]
    with connect_servers(specs) as tools:
        assert tools == []


def test_connect_servers_with_configured_remote_mocked() -> None:
    spec = MCPServerSpec(
        name="google_dev_knowledge",
        url="https://developerknowledge.googleapis.com/mcp",
        transport="sse",
        headers={"x-goog-api-key": "fake-key"},
    )
    with patch("sakthai.mcp.manager.RemoteMCPClient") as mock_client_cls:
        instance = MagicMock()
        instance.is_configured.return_value = True
        instance.as_tools.return_value = [
            Tool(
                name="google_dev_knowledge__search",
                description="Search",
                input_schema={},
                handler=lambda a, s: "ok",
            )
        ]
        mock_client_cls.return_value = instance

        with connect_servers([spec]) as tools:
            tool_names = [t.name for t in tools]
            assert "google_dev_knowledge__search" in tool_names
            # Scoped tools also generated
            assert any(n.endswith("_search") for n in tool_names)
