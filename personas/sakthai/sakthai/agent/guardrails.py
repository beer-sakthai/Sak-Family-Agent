"""Tool execution guardrails to enforce safety and policy.

This module provides a ``GuardrailPolicy`` class that can be used to check
tool calls before and after execution against a set of configurable rules.
This allows for centralized policy enforcement, such as preventing dangerous
shell commands or blocking tools based on runtime configuration.

The design is based on Phase 3 of the plan in ``PLAN.md``.
"""

from __future__ import annotations

import logging
import os
import re
import shlex
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..config import SECRET_PATTERN
from ..memory.store import MemoryStore
from .tools import Tool

logger = logging.getLogger(__name__)


class GuardrailAction(Enum):
    """The decision made by a guardrail rule."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass
class GuardrailResult:
    """The result of a guardrail check."""

    action: GuardrailAction
    reason: str | None = None
    modified_args: dict[str, Any] | None = None


PreGuardrailRule = Callable[[Tool, dict[str, Any], MemoryStore], GuardrailResult]
PostGuardrailRule = Callable[[Tool, dict[str, Any], str, bool, MemoryStore], GuardrailResult]


def _block_run_command_if_not_allowed(
    tool: Tool, _args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny the `run_command` tool if SAKTHAI_SHELL_ALLOW is not set."""
    if tool.name == "run_command" and not os.environ.get("SAKTHAI_SHELL_ALLOW"):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool 'run_command' is disabled. Set SAKTHAI_SHELL_ALLOW to enable it.",
        )
    return GuardrailResult(GuardrailAction.ALLOW)


def _is_binary(part: str, names: str | tuple[str, ...]) -> bool:
    """Return True if part matches any of the given binary names (exactly or as path suffix)."""
    if isinstance(names, str):
        names = (names,)
    return any(part == name or part.endswith(f"/{name}") for name in names)


def _is_sensitive_path(path: str) -> bool:
    """Return True if the path targets a sensitive system directory or uses traversal."""
    # Check for path traversal or home-relative paths.
    if ".." in path or path.startswith("~"):
        return True

    # Support checking flags with values like --directory=/etc
    if "=" in path and path.startswith("-"):
        _, val = path.split("=", 1)
        if _is_sensitive_path(val):
            return True

    # Support checking short flags with attached paths like -o/etc/passwd or -o~/key
    if (
        len(path) > 2
        and path.startswith("-")
        and path[1] != "-"
        and (path[2] == "/" or path[2] == "~")
    ):
        val = path[2:]
        if _is_sensitive_path(val):
            return True

    # Normalize the path to collapse redundant slashes and dots.
    # Note: os.path.normpath preserves a leading '//' on some systems, so we
    # explicitly collapse it for comparison.
    normalized = os.path.normpath(path)
    if normalized.startswith("//") and not normalized.startswith("///"):
        normalized = normalized[1:]

    if normalized.startswith("/"):
        if normalized == "/":
            return True
        # List of critical roots that should never be targeted by destructive commands.
        critical_roots = {
            "/etc",
            "/bin",
            "/sbin",
            "/usr",
            "/var",
            "/root",
            "/boot",
            "/dev",
            "/home",
            "/sys",
            "/proc",
            "/tmp",  # nosec B108 — allowlisting the root path for protection, not for temp file creation
            "/lib",
            "/lib64",
        }
        return any(normalized == c or normalized.startswith(c + "/") for c in critical_roots)
    return False


def _check_destructive_tokens(parts: list[str], context_sensitive: bool = False) -> GuardrailResult:
    """Recursively check tokens for destructive commands.

    If ``context_sensitive`` is True, discovery placeholders like '{}' and '+'
    are treated as sensitive paths (used by find -exec to target the discovered
    files).
    """
    if not parts:
        return GuardrailResult(GuardrailAction.ALLOW)

    # 1. Handle nested commands in wrappers (recursion)
    for i, part in enumerate(parts):
        # bash -c "..." or sh -c "..."
        if (
            part == "-c"
            and i > 0
            and i + 1 < len(parts)
            and _is_binary(parts[i - 1], ("bash", "sh", "zsh", "dash"))
        ):
            try:
                nested = shlex.split(parts[i + 1])
                res = _check_destructive_tokens(nested, context_sensitive=context_sensitive)
                if res.action == GuardrailAction.DENY:
                    return res
            except ValueError:
                pass

    # 2. Prevent destructive or dangerous commands on sensitive paths.
    dangerous_binaries = (
        "rm",
        "chmod",
        "mv",
        "cp",
        "ln",
        "tee",
        "chown",
        "chgrp",
        "sed",
        "curl",
        "wget",
        "cat",
        "grep",
        "head",
        "tail",
        "strings",
        "nc",
        "netcat",
        "python",
        "python3",
        "node",
    )
    for i, part in enumerate(parts):
        if _is_binary(part, dangerous_binaries):
            # Inspect tokens following the binary until a separator is hit.
            for subpart in parts[i + 1 :]:
                if subpart in (";", "&&", "||", "|"):
                    break
                if _is_sensitive_path(subpart) or (context_sensitive and subpart in ("{}", "+")):
                    binary_name = os.path.basename(part)
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially dangerous '{binary_name}' command on {subpart!r} blocked.",
                    )

    # 3. Specialized protection for dd (input/output file).
    for i, part in enumerate(parts):
        if _is_binary(part, "dd"):
            for subpart in parts[i + 1 :]:
                if subpart in (";", "&&", "||", "|"):
                    break
                if subpart.startswith("of=") or subpart.startswith("if="):
                    val = subpart[3:]
                    if _is_sensitive_path(val) or (context_sensitive and val in ("{}", "+")):
                        binary_name = os.path.basename(part)
                        op = "destructive" if subpart.startswith("of=") else "potentially dangerous"
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason=f"{op} {binary_name!r} on {val!r} blocked.",
                        )

    # 4. Prevent shell redirections targeting sensitive paths.
    for i, part in enumerate(parts):
        # We look for redirection operators (>, >>, 1>, 2>, &>, >&, >|, <, etc.)
        # Pattern: optional digit or '&', then '&>>', '>>', '>&', '>|', '<>', '<&', '>', or '<'
        # Note: longer operators must come before shorter ones to match correctly.
        match = re.search(r"(?:[0-9]|&)?(?:&>>|>>|>&|>\||<>|<&|>|<)", part)
        if match:
            # If the operator is at the end of the token or attached to its front,
            # we need to find the target path.
            target = part[match.end() :]
            if not target and i + 1 < len(parts):
                target = parts[i + 1]

            if target and (
                _is_sensitive_path(target) or (context_sensitive and target in ("{}", "+"))
            ):
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"destructive redirection to {target!r} blocked.",
                )

    # 5. Prevent 'find -delete' on sensitive paths.
    find_idx = -1
    for i, part in enumerate(parts):
        if _is_binary(part, "find"):
            find_idx = i
            break
    if find_idx != -1:
        after_find = parts[find_idx + 1 :]
        if "-delete" in after_find:
            for part in after_find:
                # Flags like -L, -H (global options) or expression flags (like -name)
                # should be skipped, not cause the whole check to stop.
                if part.startswith("-"):
                    continue
                if _is_sensitive_path(part) or (context_sensitive and part in ("{}", "+")):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"destructive 'find -delete' on {part!r} blocked.",
                    )

    # 6. Handle wrappers that don't use -c (sudo, doas, xargs, find -exec)
    for i, part in enumerate(parts):
        # sudo command ... or doas command ... or xargs command ...
        if _is_binary(part, ("sudo", "doas", "xargs")):
            res = _check_destructive_tokens(parts[i + 1 :], context_sensitive=context_sensitive)
            if res.action == GuardrailAction.DENY:
                return res
        # find ... -exec/ok command ...
        if part in ("-exec", "-execdir", "-ok", "-okdir") and any(
            _is_binary(p, "find") for p in parts[:i]
        ):
            # We don't filter out {} and + here anymore because we want the
            # recursive scanner to see them if they are being used destructively.
            # We still stop at the terminator.
            exec_args: list[str] = []
            for subpart in parts[i + 1 :]:
                if subpart in ("\\;", ";", "+"):
                    if subpart == "+":
                        exec_args.append(subpart)
                    break
                exec_args.append(subpart)

            # Heuristic: if find's target is sensitive, set context_sensitive.
            targets_sensitive = False
            for p in parts[:i]:
                if _is_sensitive_path(p):
                    targets_sensitive = True
                    break

            res = _check_destructive_tokens(exec_args, context_sensitive=targets_sensitive)
            if res.action == GuardrailAction.DENY:
                if targets_sensitive:
                    # Specific reason for find-exec when target is sensitive.
                    binary_name = os.path.basename(part)
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"destructive 'find {binary_name}' on sensitive path blocked.",
                    )
                return res

    return GuardrailResult(GuardrailAction.ALLOW)


def _block_dangerous_shell_commands(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """Deny `run_command` if it contains a potentially destructive command."""
    if tool.name != "run_command":
        return GuardrailResult(GuardrailAction.ALLOW)

    command = args.get("command", "")
    if not isinstance(command, str):
        return GuardrailResult(GuardrailAction.ALLOW)

    try:
        parts = shlex.split(command)
    except ValueError:
        return GuardrailResult(GuardrailAction.DENY, reason="Malformed shell command.")

    return _check_destructive_tokens(parts)


def _enforce_verbose_listing(
    tool: Tool, args: dict[str, Any], _store: MemoryStore
) -> GuardrailResult:
    """If `run_command` is used for `ls`, enforce the `-l` flag."""
    if tool.name == "run_command" and isinstance(args.get("command"), str):
        command = args["command"]
        if command.strip() == "ls" or (command.startswith("ls ") and "-l" not in command):
            modified_args = args.copy()
            modified_args["command"] = command.replace("ls", "ls -l", 1)
            return GuardrailResult(GuardrailAction.ALLOW, modified_args=modified_args)
    return GuardrailResult(GuardrailAction.ALLOW)


def _block_output_with_secrets(
    _tool: Tool,
    _args: dict[str, Any],
    output: str,
    _is_error: bool,
    _store: MemoryStore,
) -> GuardrailResult:
    """Deny any tool output that appears to contain a secret."""
    if re.search(SECRET_PATTERN, output):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Tool output blocked because it appears to contain a secret.",
        )
    return GuardrailResult(GuardrailAction.ALLOW)


# Default set of rules to check *before* a tool is executed.
DEFAULT_PRE_RULES: list[PreGuardrailRule] = [
    _block_run_command_if_not_allowed,
    _block_dangerous_shell_commands,
    _enforce_verbose_listing,
]

# Default set of rules to check *after* a tool is executed.
# (No default post-rules for now, but the structure is here).
DEFAULT_POST_RULES: list[PostGuardrailRule] = [
    _block_output_with_secrets,
]


@dataclass
class GuardrailPolicy:
    """A policy that enforces guardrails on tool execution."""

    pre_rules: Sequence[PreGuardrailRule] = field(default_factory=lambda: DEFAULT_PRE_RULES)
    post_rules: Sequence[PostGuardrailRule] = field(default_factory=lambda: DEFAULT_POST_RULES)

    def check_pre_execution(
        self, tool: Tool, args: dict[str, Any], store: MemoryStore
    ) -> GuardrailResult:
        """Check if a tool call is allowed before execution."""
        current_args = args
        for rule in self.pre_rules:
            result = rule(tool, current_args, store)
            if result.action == GuardrailAction.DENY:
                logger.warning(
                    "Guardrail denied pre-execution of tool %r: %s",
                    tool.name,
                    result.reason,
                )
                return result
            if result.modified_args is not None:
                current_args = result.modified_args

        # If any rule modified the args, return the final state.
        if current_args is not args:
            return GuardrailResult(GuardrailAction.ALLOW, modified_args=current_args)

        return GuardrailResult(GuardrailAction.ALLOW)

    def check_post_execution(
        self,
        tool: Tool,
        args: dict[str, Any],
        output: str,
        is_error: bool,
        store: MemoryStore,
    ) -> GuardrailResult:
        """Check if a tool's output is allowed after execution."""
        for rule in self.post_rules:
            result = rule(tool, args, output, is_error, store)
            if result.action == GuardrailAction.DENY:
                logger.warning(
                    "Guardrail denied post-execution of tool %r: %s",
                    tool.name,
                    result.reason,
                )
                return result
        return GuardrailResult(GuardrailAction.ALLOW)


DEFAULT_POLICY = GuardrailPolicy()
