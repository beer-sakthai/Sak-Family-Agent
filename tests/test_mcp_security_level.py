"""The MCP security level and the approved-server allow-list.

`MCPServerValidator.APPROVED_SERVERS` ships empty and is consulted only under
`SecurityLevel.STRICT`, while `mcp/manager.py` hardcoded `BALANCED`. So the
allow-list was unreachable, and would have denied every server if reached.
`docs/SECURITY_HARDENING_IMPLEMENTATION.md` documented `SAKTHAI_APPROVED_MCP`
and `approved_mcp_servers` as if both existed; neither did.

These tests cover the level selector, the allow-list reader, and that the
manager honors both.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.security_hardening import MCPServerValidator, SecurityLevel
from sakthai.config import approved_mcp_servers, mcp_security_level
from sakthai.mcp.manager import connect_servers
from sakthai.mcp.servers import MCPServerSpec

# --- config.mcp_security_level ----------------------------------------------


def test_security_level_defaults_to_balanced(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_SECURITY_LEVEL", raising=False)
    assert mcp_security_level() == "balanced"


@pytest.mark.parametrize("raw", ["strict", "STRICT", "  Strict  ", "balanced", "permissive"])
def test_security_level_accepts_the_three_levels(raw: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_SECURITY_LEVEL", raw)
    assert mcp_security_level() == raw.strip().lower()


@pytest.mark.parametrize("raw", ["", "paranoid", "1", "true"])
def test_unrecognised_security_level_falls_back_to_balanced(
    raw: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A typo must not fail a launch — but note it yields less enforcement."""
    monkeypatch.setenv("SAKTHAI_MCP_SECURITY_LEVEL", raw)
    assert mcp_security_level() == "balanced"


# --- config.approved_mcp_servers --------------------------------------------


def test_approved_servers_unset_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_APPROVED_MCP", raising=False)
    assert approved_mcp_servers() == frozenset()


@pytest.mark.parametrize(
    "raw",
    [
        "playwright,stepsecurity",
        "playwright stepsecurity",
        "playwright, stepsecurity",
        " playwright ,, stepsecurity ",
    ],
)
def test_approved_servers_accepts_comma_or_space(raw: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Same separator convention as SAKTHAI_WITH_SKILLS and SAKTHAI_MAIL_ALLOW."""
    monkeypatch.setenv("SAKTHAI_APPROVED_MCP", raw)
    assert approved_mcp_servers() == frozenset({"playwright", "stepsecurity"})


# --- the validator's strict path --------------------------------------------


def test_strict_denies_everything_when_allowlist_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fail-closed direction: no allow-list means no external servers."""
    monkeypatch.delenv("SAKTHAI_APPROVED_MCP", raising=False)
    ok, reason = MCPServerValidator.validate_server_config(
        {"name": "playwright", "command": "npx", "args": []}, SecurityLevel.STRICT
    )
    assert not ok
    assert "allows no servers" in reason


def test_strict_admits_a_server_named_in_the_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_APPROVED_MCP", "playwright")
    ok, _ = MCPServerValidator.validate_server_config(
        {"name": "playwright", "command": "npx", "args": []}, SecurityLevel.STRICT
    )
    assert ok


def test_strict_still_rejects_an_unlisted_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_APPROVED_MCP", "playwright")
    ok, reason = MCPServerValidator.validate_server_config(
        {"name": "something-else", "command": "npx", "args": []}, SecurityLevel.STRICT
    )
    assert not ok
    assert "playwright" in reason  # the hint lists what *is* approved


def test_strict_still_applies_the_command_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Being on the allow-list does not exempt a spec from the argv scan."""
    monkeypatch.setenv("SAKTHAI_APPROVED_MCP", "shell")
    ok, reason = MCPServerValidator.validate_server_config(
        {"name": "shell", "command": "sh", "args": ["-c", "rm -rf /"]},
        SecurityLevel.STRICT,
    )
    assert not ok
    assert "suspicious pattern" in reason


# --- the manager honors the level ------------------------------------------


def test_manager_runs_balanced_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_MCP_SECURITY_LEVEL", raising=False)
    monkeypatch.delenv("SAKTHAI_APPROVED_MCP", raising=False)
    spec = MCPServerSpec(name="ok-server", command="node", args=["server.js"])
    mock_client = MagicMock()
    mock_client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()


def test_manager_strict_skips_an_unapproved_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strict mode is now reachable, and fails soft like every other rejection."""
    monkeypatch.setenv("SAKTHAI_MCP_SECURITY_LEVEL", "strict")
    monkeypatch.delenv("SAKTHAI_APPROVED_MCP", raising=False)
    spec = MCPServerSpec(name="unapproved", command="node", args=["server.js"])
    with (
        patch("sakthai.mcp.manager.StdioMCPClient") as MockStdio,
        connect_servers([spec]) as tools,
    ):
        assert tools == []
    MockStdio.assert_not_called()


def test_manager_strict_starts_an_approved_server(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_MCP_SECURITY_LEVEL", "strict")
    monkeypatch.setenv("SAKTHAI_APPROVED_MCP", "approved")
    spec = MCPServerSpec(name="approved", command="node", args=["server.js"])
    mock_client = MagicMock()
    mock_client.as_tools.return_value = []
    with (
        patch("sakthai.mcp.manager.StdioMCPClient", return_value=mock_client) as MockStdio,
        connect_servers([spec]),
    ):
        pass
    MockStdio.assert_called_once()
