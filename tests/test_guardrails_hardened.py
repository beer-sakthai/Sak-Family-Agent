"""Hardened guardrail tests for shell commands."""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "command",
    [
        "find /etc -delete",
        "find / -delete",
        "find ~ -delete",
        "find /etc -name 'foo' -delete",
        "find /var/log -type f -delete",
        "find /usr/bin -delete",
    ],
)
def test_find_delete_on_sensitive_paths_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "find -delete" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "rm /etc/passwd",
        "rm ~/some_sensitive_file",
        "chmod 777 /etc/shadow",
        "chmod 000 /bin/ls",
        "mv /etc/hosts /tmp/hosts",
        "mv ~/.ssh/id_rsa /tmp/key",
        "rm ../../../etc/passwd",
    ],
)
def test_non_recursive_destructive_on_sensitive_paths_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and ("destructive" in result.reason or "blocked" in result.reason)


@pytest.mark.parametrize(
    "command",
    [
        "find /etc -exec rm {} +",
        "find / -exec rm {} \\;",
        "find ~ -exec chmod 777 {} +",
        "find /usr -exec mv {} /tmp +",
    ],
)
def test_find_exec_destructive_on_sensitive_paths_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and any(
        s in result.reason for s in ("find -exec", "Potentially destructive", "destructive")
    )


@pytest.mark.parametrize(
    "command",
    [
        "find ./local-dir -delete",
        "rm ./local-file",
        "chmod +x script.sh",
        "mv old.txt new.txt",
        "find . -name '*.txt' -exec cat {} +",
    ],
)
def test_safe_commands_still_allowed(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW
