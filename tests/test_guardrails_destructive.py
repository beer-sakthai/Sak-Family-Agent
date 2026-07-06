"""Tests for the destructive shell command guardrails."""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import (
    GuardrailAction,
    GuardrailPolicy,
    _is_sensitive_path,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/", True),
        ("/etc", True),
        ("/etc/shadow", True),
        ("/bin", True),
        ("/bin/ls", True),
        ("/home", True),
        ("/home/user", True),
        ("/tmp", True),
        ("/tmp/file", True),
        ("/usr/lib", True),
        ("/lib64", True),
        ("~", True),
        ("~/Documents", True),
        ("../etc", True),
        ("./../etc", True),
        ("safe_dir", False),
        ("/var/log/app.log", True),
        ("/boot/vmlinuz", True),
        ("/proc/cpuinfo", True),
        ("/sys/class", True),
    ],
)
def test_is_sensitive_path(path: str, expected: bool) -> None:
    """Verify that sensitive paths are correctly identified."""
    assert _is_sensitive_path(path) == expected


@pytest.mark.parametrize(
    "command",
    [
        "find / -delete",
        "find /etc -delete",
        "find /home -name '*.old' -delete",
        "find ~ -delete",
        "find /tmp -delete",
        "find ../ -delete",
        "sudo find /bin -delete",
        "find /usr/sbin -type f -delete",
    ],
)
def test_find_delete_denied(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """find -delete on sensitive paths is blocked."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "find -delete" in result.reason
    assert "sensitive path" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "find . -delete",
        "find ./local_dir -delete",
        "find my_project -name '*.tmp' -delete",
    ],
)
def test_find_delete_allowed_on_safe_paths(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """find -delete on non-sensitive paths is allowed."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "find / -exec rm -rf {} +",
        "find /etc -exec chmod -R 777 {} \\;",
        "find /bin -exec mv {} local_bak \\;",
        "find ~ -exec rm -r {} +",
        "find ../ -exec rm -rf {} +",
    ],
)
def test_find_exec_destructive_denied(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """find -exec with destructive commands on sensitive paths is blocked."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "find -exec" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf /lib",
        "rm -r /lib64",
        "chmod -R 755 /var",
        "mv /boot /mnt/usb",
        "rm -rf /sys/kernel",
        "rm -rf /proc/123",
    ],
)
def test_newly_protected_paths_denied(
    command: str,
    run_command_tool: Tool,
    store: MemoryStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify that newly added sensitive paths are also protected for rm/chmod/mv."""
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    policy = GuardrailPolicy()
    result = policy.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert "Potentially destructive" in result.reason
