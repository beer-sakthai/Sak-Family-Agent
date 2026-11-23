"""Regression tests: external MCP tools must not escape the name-keyed rules.

Tools merged in from an external MCP server are namespaced ``<server>__<tool>``
by ``mcp/manager.py``. Every rule in ``agent/guardrails.py`` that keys off a
specific tool keys off a bare built-in name, so against the raw namespaced name
each one used to fall through to ALLOW. A server named ``shell`` offering
``run_command`` was therefore exempt from the ``SAKTHAI_SHELL_ALLOW`` opt-in and
from the destructive-token scanning, while the blunter
``_block_sensitive_path_args`` rule — which exempts only the *literal*
``run_command`` — applied to it instead. The precise rules were skipped and the
imprecise one fired.

These tests pin the fix in both directions: the namespaced name is now matched,
and normalization has not loosened anything for genuinely unrelated tools.
"""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    effective_tool_name,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


def _tool(name: str) -> Tool:
    return Tool(name, "desc", {}, lambda _a, _s: "")


# --- effective_tool_name -----------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("run_command", "run_command"),  # bare built-in, untouched
        ("shell__run_command", "run_command"),  # the reported bypass
        ("mcp-shell__run_command", "run_command"),  # hyphenated server name
        ("a__b__c", "b__c"),  # first separator splits; server name is the prefix
        ("search_sessions", "search_sessions"),  # single underscores survive
        ("__leading", "__leading"),  # empty server name is not a namespace
        ("trailing__", "trailing__"),  # empty tool name is not a namespace
        ("__", "__"),
        ("", ""),
    ],
)
def test_effective_tool_name(raw: str, expected: str) -> None:
    assert effective_tool_name(raw) == expected


def test_no_builtin_tool_name_contains_the_separator() -> None:
    """The premise that makes stripping unambiguous.

    If a built-in ever gains a `__` in its name, `effective_tool_name` would
    start mangling it and this test is the warning.
    """
    from sakthai.agent.tools import BUILTIN_TOOLS

    offenders = [t.name for t in BUILTIN_TOOLS if "__" in t.name]
    assert offenders == [], f"built-in tool names must not contain '__': {offenders}"


# --- the shell opt-in gate ---------------------------------------------------


def test_namespaced_run_command_is_gated_by_shell_allow(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An external server's run_command needs the same opt-in as the built-in."""
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("shell__run_command"), {"command": "ls"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "SAKTHAI_SHELL_ALLOW" in result.reason


def test_namespaced_run_command_allowed_once_opted_in(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("shell__run_command"), {"command": "ls -l"}, store
    )
    assert result.action == GuardrailAction.ALLOW


# --- destructive-command scanning -------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "cat ~/.ssh/id_rsa",
        "cat /etc/shadow",
    ],
)
def test_namespaced_run_command_is_scanned_for_destructive_tokens(
    command: str, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With the opt-in granted, the command itself must still be scanned.

    This is the half that mattered most: before the fix these reached the
    handler of an external server unexamined.
    """
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("shell__run_command"), {"command": command}, store
    )
    assert result.action == GuardrailAction.DENY, f"{command!r} was not blocked"


def test_namespaced_and_builtin_run_command_agree(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The two names must reach the same decision for the same arguments."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    args = {"command": "rm -rf /"}
    builtin = DEFAULT_POLICY.check_pre_execution(_tool("run_command"), dict(args), store)
    external = DEFAULT_POLICY.check_pre_execution(_tool("srv__run_command"), dict(args), store)
    assert builtin.action == external.action == GuardrailAction.DENY


# --- the mail allow-list -----------------------------------------------------


def test_namespaced_mail_tool_honours_the_allowlist(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SAKTHAI_MAIL_ALLOW unset denies every recipient, external tools included.

    The recipient comes from the model, so an injected instruction reaching an
    external mail server must not bypass the operator's allow-list.
    """
    monkeypatch.delenv("SAKTHAI_MAIL_ALLOW", raising=False)
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("m365__send_outlook_mail"),
        {"to": "attacker@example.com", "subject": "s", "body": "b"},
        store,
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "allow-list" in result.reason


def test_namespaced_mail_tool_allowed_when_listed(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_MAIL_ALLOW", "@example.com")
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("m365__send_outlook_mail"),
        {"to": "someone@example.com", "subject": "s", "body": "b"},
        store,
    )
    assert result.action == GuardrailAction.ALLOW


# --- normalization must not loosen anything ---------------------------------


def test_unrelated_external_tool_still_gets_the_path_rule(store: MemoryStore) -> None:
    """Only `run_command` is exempted from the sensitive-path scan.

    An external tool with some other name keeps the generic protection — the
    fix narrows which rule applies to a namespaced `run_command`, it does not
    exempt external tools at large.
    """
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("files__fetch"), {"path": "~/.ssh/id_rsa"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "sensitive path" in result.reason


def test_external_tool_whose_bare_name_is_harmless_is_allowed(store: MemoryStore) -> None:
    result = DEFAULT_POLICY.check_pre_execution(
        _tool("docs__microsoft_docs_search"), {"query": "mcp"}, store
    )
    assert result.action == GuardrailAction.ALLOW
