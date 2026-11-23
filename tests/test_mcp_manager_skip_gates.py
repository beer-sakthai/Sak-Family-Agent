"""The three gates that stop a configured MCP server from being started.

`connect_servers()` fails soft: a server it cannot or should not start is
logged and skipped, never raised. Three independent reasons, all added with
the built-in ecosystem servers but applying to **every** spec, including the
config-driven `npx` servers that predate them:

* the remote credential check (`is_configured()`), before any network I/O;
* the Node toolchain check, for `npx`/`node`/`npm` commands;
* the genkit environment opt-in.

They were untested. A skip gate that stops working fails open and silently —
the server starts anyway — so it is exactly the kind of thing that needs a test
rather than a reading.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sakthai.mcp.manager import connect_servers
from sakthai.mcp.servers import STREAMABLE_HTTP, MCPServerSpec

# --- the Node toolchain gate -------------------------------------------------


@pytest.mark.parametrize("command", ["npx", "node", "npm"])
def test_missing_node_toolchain_skips_the_server(command: str) -> None:
    """Without the binary the spawn would fail anyway; skipping says why."""
    spec = MCPServerSpec(name="needs-node", command=command, args=["-y", "thing@1.0.0"])
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value=None),
        patch("sakthai.mcp.manager.StdioMCPClient") as MockStdio,
        connect_servers([spec]) as tools,
    ):
        assert tools == []
    MockStdio.assert_not_called()


def test_a_present_toolchain_does_not_skip() -> None:
    spec = MCPServerSpec(name="needs-node", command="npx", args=["-y", "thing@1.0.0"])
    client = MagicMock()
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value="/usr/bin/npx"),
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()


def test_a_non_node_command_is_not_toolchain_gated() -> None:
    """The gate names three binaries; anything else is the caller's business."""
    spec = MCPServerSpec(name="other", command="/usr/bin/my-server")
    client = MagicMock()
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value=None),
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()


# --- the genkit environment opt-in -------------------------------------------

_GENKIT_VARS = ("GENKIT_ENV", "GENKIT_PROJECT_ID", "FIREBASE_PROJECT_ID", "SAKTHAI_ENABLE_GENKIT")


@pytest.fixture
def _no_genkit_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in _GENKIT_VARS:
        monkeypatch.delenv(var, raising=False)


def test_genkit_is_skipped_without_an_environment(_no_genkit_env: None) -> None:
    spec = MCPServerSpec(name="genkit", command="npx", args=["-y", "genkit@1.44.0", "mcp"])
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value="/usr/bin/npx"),
        patch("sakthai.mcp.manager.StdioMCPClient") as MockStdio,
        connect_servers([spec]) as tools,
    ):
        assert tools == []
    MockStdio.assert_not_called()


@pytest.mark.parametrize("var", _GENKIT_VARS)
def test_any_one_genkit_variable_opts_in(
    var: str, _no_genkit_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(var, "1")
    spec = MCPServerSpec(name="genkit", command="npx", args=["-y", "genkit@1.44.0", "mcp"])
    client = MagicMock()
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value="/usr/bin/npx"),
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()


def test_the_genkit_gate_is_keyed_on_the_name_only(_no_genkit_env: None) -> None:
    """A differently named server running the same package is not gated."""
    spec = MCPServerSpec(name="not-genkit", command="npx", args=["-y", "genkit@1.44.0", "mcp"])
    client = MagicMock()
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.shutil.which", return_value="/usr/bin/npx"),
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()


# --- the scoped google-dev tools --------------------------------------------


def test_google_dev_knowledge_gains_scoped_search_tools() -> None:
    """The five `site:`-scoped tools are synthesized alongside the server's own."""
    spec = MCPServerSpec(
        name="google_dev_knowledge",
        url="https://developerknowledge.googleapis.com/mcp",
        transport=STREAMABLE_HTTP,
    )
    client = MagicMock()
    client.is_configured.return_value = True
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.RemoteMCPClient", return_value=client),
        connect_servers([spec]) as tools,
    ):
        names = {t.name for t in tools}
    assert len(names) == 5, names
    assert all(n.startswith("google_dev_knowledge__") for n in names)
    assert any(n.endswith("_chrome_dev_search") for n in names)


def test_a_failure_synthesising_scoped_tools_is_not_fatal() -> None:
    """The server's own tools must survive a problem with the extras."""
    spec = MCPServerSpec(
        name="google_dev_knowledge",
        url="https://developerknowledge.googleapis.com/mcp",
        transport=STREAMABLE_HTTP,
    )
    client = MagicMock()
    client.is_configured.return_value = True
    client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.RemoteMCPClient", return_value=client),
        patch("sakthai.mcp.manager.create_scoped_google_dev_tools", side_effect=RuntimeError),
        connect_servers([spec]) as tools,
    ):
        assert tools == []
