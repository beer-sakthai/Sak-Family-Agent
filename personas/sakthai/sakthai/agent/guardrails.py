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
    """Return True if the path is a system-critical or sensitive location."""
    if path.startswith("~") or ".." in path:
        return True

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
        "/tmp",  # nosec B108 — this is a protection list, not a target
        "/lib",
        "/lib64",
    }
    if path == "/":
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
    return any(path == root or path.startswith(root + "/") for root in critical_roots)


def _check_destructive_tokens(parts: list[str]) -> GuardrailResult:
    """Recursively check tokens for destructive commands."""
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
                res = _check_destructive_tokens(nested)
                if res.action == GuardrailAction.DENY:
                    return res
            except ValueError:
                pass

    # 2. Prevent recursive deletion of absolute or home-relative paths.
    rm_idx = -1
    for i, part in enumerate(parts):
        if _is_binary(part, "rm"):
            rm_idx = i
            break
    if rm_idx != -1:
        after_rm = parts[rm_idx + 1 :]
        # Look for recursive flag among the arguments.
        has_recursive = any(
            (p.startswith("-") and not p.startswith("--") and ("r" in p or "R" in p))
            or p == "--recursive"
            for p in after_rm
        )
        if has_recursive:
            for part in after_rm:
                if _is_sensitive_path(part):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially destructive 'rm' command on {part!r} blocked.",
                    )

    # 3. Prevent recursive chmod on sensitive paths.
    chmod_idx = -1
    for i, part in enumerate(parts):
        if _is_binary(part, "chmod"):
            chmod_idx = i
            break
    if chmod_idx != -1:
        after_chmod = parts[chmod_idx + 1 :]
        has_recursive = any(
            (p.startswith("-") and not p.startswith("--") and "R" in p) or p == "--recursive"
            for p in after_chmod
        )
        if has_recursive:
            for part in after_chmod:
                if _is_sensitive_path(part):
                    return GuardrailResult(
                        GuardrailAction.DENY,
                        reason=f"Potentially destructive 'chmod' command on {part!r} blocked.",
                    )

    # 4. Prevent moving critical system directories.
    mv_idx = -1
    for i, part in enumerate(parts):
        if _is_binary(part, "mv"):
            mv_idx = i
            break
    if mv_idx != -1:
        after_mv = parts[mv_idx + 1 :]
        for part in after_mv:
            if _is_sensitive_path(part):
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"Potentially destructive 'mv' command on {part!r} blocked.",
                )

    # 5. Handle wrappers that don't use -c (sudo, doas, find -exec)
    for i, part in enumerate(parts):
        # sudo command ... or doas command ...
        if _is_binary(part, ("sudo", "doas")):
            res = _check_destructive_tokens(parts[i + 1 :])
            if res.action == GuardrailAction.DENY:
                return res
        # find ... -delete or -exec command ...
        if (part == "-delete" or part == "-exec") and any(_is_binary(p, "find") for p in parts[:i]):
            # Check if find's target is sensitive.
            targets_sensitive_path = None
            for p in parts[:i]:
                # find targets are usually paths before the first flag.
                if not p.startswith("-") and not _is_binary(p, "find") and _is_sensitive_path(p):
                    targets_sensitive_path = p
                    break

            if part == "-delete" and targets_sensitive_path:
                return GuardrailResult(
                    GuardrailAction.DENY,
                    reason=f"destructive 'find -delete' on sensitive path {targets_sensitive_path!r} blocked.",
                )

            if part == "-exec":
                # Filter out find-specific tokens like {} and + or \;
                filtered_parts = [p for p in parts[i + 1 :] if p not in ("{}", "+", "\\;", ";")]

                # If find targets sensitive path, and we are doing recursive rm/chmod or any mv,
                # block it even if the exec part doesn't explicitly name the path (uses {}).
                if targets_sensitive_path:
                    if any(_is_binary(p, "rm") for p in filtered_parts) and any(
                        (p.startswith("-") and "r" in p.replace("-", "")) or p == "--recursive"
                        for p in filtered_parts
                    ):
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason="destructive 'find -exec rm' on sensitive path blocked.",
                        )
                    if any(_is_binary(p, "chmod") for p in filtered_parts) and any(
                        (p.startswith("-") and "R" in p.replace("-", "")) or p == "--recursive"
                        for p in filtered_parts
                    ):
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason="destructive 'find -exec chmod' on sensitive path blocked.",
                        )
                    if any(_is_binary(p, "mv") for p in filtered_parts):
                        return GuardrailResult(
                            GuardrailAction.DENY,
                            reason="destructive 'find -exec mv' on sensitive path blocked.",
                        )

                res = _check_destructive_tokens(filtered_parts)
                if res.action == GuardrailAction.DENY:
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
    # A regex for common API key prefixes (sk-, rk-, pk-, ghp-, hf-), Google keys (AIza),
    # and Telegram bot tokens (123456789:ABC...).
    # Handles both underscore (sk_) and hyphen (sk-) used by Anthropic, OpenAI, and HF.
    secret_pattern = r"\b(?:(?:sk|rk|pk|ghp|hf)[-_][a-zA-Z0-9\-_]{20,}|AIza[0-9A-Za-z\-_]{34,}|[0-9]{8,12}:[a-zA-Z0-9_-]{35})\b"  # nosec B105
    if re.search(secret_pattern, output):
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
