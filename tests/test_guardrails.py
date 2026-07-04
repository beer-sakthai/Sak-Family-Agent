"""Tests for the agent guardrails."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    GuardrailPolicy,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.fixture
def learn_tool() -> Tool:
    return Tool("learn", "desc", {}, lambda _a, _s: "")


def test_policy_allows_safe_tool(learn_tool: Tool, store: MemoryStore) -> None:
    """A tool not targeted by any rule should be allowed."""
    result = DEFAULT_POLICY.check_pre_execution(learn_tool, {}, store)
    assert result.action == GuardrailAction.ALLOW


def test_run_command_denied_by_default(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_command is denied if SAKTHAI_SHELL_ALLOW is not set."""
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "ls"}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "disabled" in result.reason


def test_run_command_allowed_when_env_var_is_set(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """run_command is allowed if SAKTHAI_SHELL_ALLOW is set."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "ls -l"}, store)
    assert result.action == GuardrailAction.ALLOW


def test_other_tools_unaffected_by_shell_env_var(
    learn_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The SAKTHAI_SHELL_ALLOW check should only apply to run_command."""
    monkeypatch.delenv("SAKTHAI_SHELL_ALLOW", raising=False)
    result = DEFAULT_POLICY.check_pre_execution(learn_tool, {}, store)
    assert result.action == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /",
        "rm -rf ~",
        "rm -rf /etc",
        "rm -r -f /usr",
        "rm --recursive --force /var",
        "rm -fr /tmp",
        "sudo rm -rf /",
        "sudo rm -rf /etc",
        "rm -Rf /lib",
    ],
)
def test_dangerous_shell_commands_are_denied(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Even with shell enabled, destructive commands are blocked."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()  # Use default rules
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "destructive" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "ls -l",
        "git status",
        "rm -rf ./temp-dir",  # Not at a root level
        "echo 'hello'",
    ],
)
def test_safe_shell_commands_are_allowed(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Benign commands should pass the guardrails when shell is enabled."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW


def test_malformed_shell_command_is_denied(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A command that shlex cannot parse should be denied."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": "echo 'mismatched"}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "Malformed" in result.reason


def test_custom_rules_can_be_added(learn_tool: Tool, store: MemoryStore) -> None:
    """Verify that a custom rule can be used to deny a tool."""

    from sakthai.agent.guardrails import GuardrailResult

    def _deny_all_rule(tool: Tool, args: dict[str, Any], store: MemoryStore) -> GuardrailResult:
        return GuardrailResult(action=GuardrailAction.DENY, reason="custom rule")

    policy = GuardrailPolicy(pre_rules=[_deny_all_rule])
    result = policy.check_pre_execution(learn_tool, {}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason == "custom rule"
