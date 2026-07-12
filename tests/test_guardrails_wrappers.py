"""Guardrail tests for transparent-wrapper flag handling and find write variants.

These target the previously unexercised bypass-relevant branches:
the flag-argument skipping heuristics for transparent wrappers (timeout,
nice, ionice, chrt, taskset, stdbuf, sudo, doas, env), the destructive
``find -fprint*`` file-writing variants, the find handling after a command
separator, and the separator/short-flag/wildcard branches of
``_is_sensitive_path``.
"""

from __future__ import annotations

import pytest

from sakthai.agent.guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    _is_sensitive_path,
)
from sakthai.agent.tools import Tool
from sakthai.memory.store import MemoryStore


@pytest.fixture
def run_command_tool() -> Tool:
    return Tool("run_command", "desc", {}, lambda _a, _s: "")


def _check(tool: Tool, store: MemoryStore, command: str) -> GuardrailAction:
    result = DEFAULT_POLICY.check_pre_execution(tool, {"command": command}, store)
    return result.action


# ---------------------------------------------------------------------------
# Transparent wrappers: flag arguments must be skipped, not treated as the
# wrapped command, and the wrapper must never launder a destructive command.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "timeout -s KILL -k 3 5 echo ok",
        "timeout --signal TERM 10 echo ok",
        "timeout 5 echo ok",
        "nice -n 10 echo ok",
        "nice --adjustment 5 echo ok",
        "ionice -c 2 -n 7 echo ok",
        "chrt -p 99 echo ok",
        "taskset -c 0 echo ok",
        "taskset -p 1234 echo ok",
        "stdbuf -o L echo ok",
        "stdbuf -i 0 -e 0 echo ok",
        "sudo -u deploy echo ok",
        "sudo -g staff echo ok",
        "sudo -- echo ok",
        "doas -u deploy echo ok",
        "env VAR=1 OTHER=2 echo ok",
        "env -i PATH=/usr/bin echo ok",
        "nohup echo ok",
        "setsid echo ok",
        "xargs echo",
    ],
)
def test_wrapper_flag_arguments_with_benign_command_allowed(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    assert _check(run_command_tool, store, command) == GuardrailAction.ALLOW


@pytest.mark.parametrize(
    "command",
    [
        "timeout -s KILL 5 rm -rf /etc",
        "timeout --signal TERM 10 shred /etc/passwd",
        "timeout 5 rm -rf /usr",
        "nice -n 19 shred /etc/passwd",
        "ionice -c 2 -n 7 rm -rf /var",
        "chrt -p 99 rm /etc/hosts",
        "taskset -c 0 rm -rf /boot",
        "stdbuf -o L tee /etc/cron.d/evil",
        "sudo -u root rm -rf /usr",
        "sudo -- rm -rf /etc",
        "doas -u root rm /etc/passwd",
        "env PATH=/tmp rm -rf /var",
        "env -i rm /etc/shadow",
        "xargs rm -rf /etc",
        "nohup rm -rf /home",
        "setsid shred /etc/shadow",
    ],
)
def test_wrapper_does_not_launder_destructive_command(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    assert _check(run_command_tool, store, command) == GuardrailAction.DENY


# ---------------------------------------------------------------------------
# find file-writing variants (-fprint, -fprint0, -fls, -fprintf)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "find . -name '*.conf' -fprint /etc/cron.d/evil",
        "find . -fprint0 /etc/evil",
        "find . -type f -fls /root/.findlog",
        "find . -fprintf /etc/evil '%p'",
    ],
)
def test_find_write_variants_to_sensitive_paths_blocked(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "destructive 'find" in result.reason


def test_find_write_variant_to_local_file_allowed(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    command = "find . -name '*.txt' -fprint results.txt"
    assert _check(run_command_tool, store, command) == GuardrailAction.ALLOW


# ---------------------------------------------------------------------------
# find across command separators
# ---------------------------------------------------------------------------


def test_find_scan_stops_at_separator_and_allows_benign_tail(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    command = "find . -name tmp ; echo done"
    assert _check(run_command_tool, store, command) == GuardrailAction.ALLOW


def test_second_find_with_sensitive_exec_target_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The first find is benign and its discovery scan stops at ';', so only
    # the -exec handler (which sees the sensitive /etc target of the second
    # find) can catch this.
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    command = "find . -name tmp ; find /etc -exec rm {} +"
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "sensitive path" in result.reason


def test_wrapped_second_find_discovering_sensitive_root_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The top-level find scan stops at ';', so the sensitive discovery is only
    # visible when the wrapper handler recursively re-checks sudo's tail.
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    command = "find . -name tmp ; sudo find /etc"
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "'find'" in result.reason


def test_find_exec_spawning_second_find_on_sensitive_root_blocked(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Local find target, but the -exec payload is itself a find over /etc:
    # the nested denial propagates as-is (no find-exec-specific reason).
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    command = "find . -name tmp ; find . -exec find /etc \\;"
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": command}, store)
    assert result.action == GuardrailAction.DENY
    assert result.reason and "'find' command on '/etc'" in result.reason


@pytest.mark.parametrize(
    "command",
    [
        "bash -c 'echo hi'",
        "eval 'echo hi'",
        "python -c 'print(open(\"/workspace/data.txt\"))'",
        "dd bs=4096 count=1",
        "find . -exec echo {} ;",
        "find . -exec echo {}",
    ],
)
def test_nested_and_exec_scans_allow_benign_commands(
    command: str, run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    assert _check(run_command_tool, store, command) == GuardrailAction.ALLOW


def test_bare_ls_is_rewritten_to_verbose_listing(
    run_command_tool: Tool, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_SHELL_ALLOW", "1")
    result = DEFAULT_POLICY.check_pre_execution(run_command_tool, {"command": "ls"}, store)
    assert result.action == GuardrailAction.ALLOW
    assert result.modified_args is not None
    assert result.modified_args["command"] == "ls -l"


# ---------------------------------------------------------------------------
# _is_sensitive_path separator, short-flag, and wildcard branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        # curl-style upload prefix: '@' at position 0 is a prefix, not a separator.
        ("@/etc/passwd", True),
        ("@localfile", False),
        # --flag=value and prog:value separators.
        ("--out=/etc/passwd", True),
        ("--out=build/report.txt", False),
        ("FILE:/etc/passwd", True),
        ("of=memory.db", True),
        # Short flags with attached paths.
        ("-o/etc/passwd", True),
        ("-o~/secrets", True),
        ("-o/workspace/output.txt", False),
        # Wildcards.
        ("/etc/*", True),
        ("/et*", True),  # prefix of the critical root /etc
        ("/*", True),  # base path '/' is itself sensitive
        ("/zzz*", False),  # prefix of no critical root
        # Traversal and home-relative.
        ("../secrets", True),
        ("~/.ssh/id_rsa", True),
    ],
)
def test_is_sensitive_path_separator_and_wildcard_branches(path: str, expected: bool) -> None:
    assert _is_sensitive_path(path) is expected


def test_is_sensitive_path_leading_wildcard_depends_on_allow_local() -> None:
    # A path that is nothing but a wildcard can target anything in the local
    # directory: blocked for destructive use, allowed for read-style use.
    assert _is_sensitive_path("*") is True
    assert _is_sensitive_path("*.txt", allow_local=True) is False
