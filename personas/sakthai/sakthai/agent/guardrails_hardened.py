"""Enhanced guardrails with security hardening integration.

This module wraps the base guardrails with additional protections from
security_hardening.py to defend against identified attack vectors.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..memory.store import MemoryStore
from .guardrails import (
    DEFAULT_POLICY,
    GuardrailAction,
    GuardrailResult,
    _block_run_command_if_not_allowed,
)
from .security_hardening import (
    ConfigFileIntegrity,
    EnhancedPathValidator,
    MCPServerValidator,
    SecurityLevel,
    ShellCommandHardener,
    SymlinkDetector,
    get_audit_logger,
    pin_environment,
    verify_environment,
)
from .tools import Tool

logger = logging.getLogger(__name__)

# Global config integrity monitor
_config_integrity: ConfigFileIntegrity | None = None


def initialize_hardened_guardrails(security_level: SecurityLevel = SecurityLevel.BALANCED) -> None:
    """Initialize the hardened guardrails system.

    Should be called once at agent startup.

    Args:
        security_level: Level of security hardening (STRICT/BALANCED/PERMISSIVE)
    """
    global _config_integrity

    # Pin environment variables
    pin_environment()
    logger.info(f"Hardened guardrails initialized at security level: {security_level.value}")

    # Initialize config file integrity monitoring
    _config_integrity = ConfigFileIntegrity()

    # Check initial config file permissions
    perm_events = _config_integrity.check_permissions()
    for event in perm_events:
        logger.warning(f"Security warning: {event.message}")
        get_audit_logger().log_event(event)


def check_environment_integrity() -> GuardrailResult:
    """Check for environment variable tampering.

    Returns:
        GuardrailResult denying if tampering detected
    """
    events = verify_environment()
    if events:
        for event in events:
            logger.warning(f"Security alert: {event.message}")
            get_audit_logger().log_event(event)
        return GuardrailResult(
            GuardrailAction.DENY, reason="Environment variable tampering detected"
        )
    return GuardrailResult(GuardrailAction.ALLOW)


def check_config_integrity() -> GuardrailResult:
    """Check for config file tampering.

    Returns:
        GuardrailResult denying if tampering detected
    """
    if _config_integrity is None:
        return GuardrailResult(GuardrailAction.ALLOW)

    events = _config_integrity.verify()
    events.extend(_config_integrity.check_permissions())

    if events:
        for event in events:
            logger.warning(f"Security alert: {event.message}")
            get_audit_logger().log_event(event)
        return GuardrailResult(GuardrailAction.DENY, reason="Configuration file tampering detected")

    return GuardrailResult(GuardrailAction.ALLOW)


def check_enhanced_path_safety(path: str) -> GuardrailResult:
    """Enhanced path safety check with Unicode, glob, and case-sensitivity handling.

    Args:
        path: Path to validate

    Returns:
        GuardrailResult denying if unsafe patterns detected
    """
    # Normalize path in all Unicode forms
    normalized_forms = EnhancedPathValidator.normalize_path_thoroughly(path)

    # Check all normalized forms for sensitivity
    from .guardrails import _is_sensitive_path

    for norm_path in normalized_forms:
        if _is_sensitive_path(norm_path):
            return GuardrailResult(
                GuardrailAction.DENY, reason=f"Path targets sensitive location: {path}"
            )

    # Check for glob/wildcard patterns
    glob_patterns = EnhancedPathValidator.detect_glob_patterns(path)
    if glob_patterns:
        return GuardrailResult(
            GuardrailAction.DENY,
            reason=f"Path contains potentially dangerous glob patterns: {', '.join(glob_patterns)}",
        )

    # Check for case-sensitivity tricks
    if EnhancedPathValidator.check_case_sensitivity(path):
        return GuardrailResult(
            GuardrailAction.DENY,
            reason="Path uses case-sensitive tricks (e.g., .SSH vs .ssh)",
        )

    return GuardrailResult(GuardrailAction.ALLOW)


def check_symlink_safety(path: str) -> GuardrailResult:
    """Check for symlink-based traversal attacks.

    Args:
        path: Path to check

    Returns:
        GuardrailResult denying if dangerous symlinks detected
    """
    path_obj = Path(path).expanduser()

    # Detect symlinks
    if SymlinkDetector.is_symlink(path_obj):
        events = SymlinkDetector.detect_dangerous_symlinks(path)
        if events:
            for event in events:
                logger.warning(f"Security alert: {event.message}")
                get_audit_logger().log_event(event)
            return GuardrailResult(
                GuardrailAction.DENY, reason=f"Dangerous symlink detected: {path}"
            )

    # Check all parent directories for symlinks
    current = path_obj
    while current != current.parent:
        if SymlinkDetector.is_symlink(current):
            return GuardrailResult(
                GuardrailAction.DENY,
                reason=f"Parent directory is a symlink: {current}",
            )
        current = current.parent

    return GuardrailResult(GuardrailAction.ALLOW)


def check_shell_command_hardened(command: str) -> GuardrailResult:
    """Enhanced shell command checking for heredoc and continuation bypass attempts.

    Args:
        command: Shell command to validate

    Returns:
        GuardrailResult denying if bypass patterns detected
    """
    # Check for heredoc patterns
    heredocs = ShellCommandHardener.detect_heredoc(command)
    if heredocs:
        # Heredocs could hide destructive commands, expand and re-check
        expanded = ShellCommandHardener.expand_line_continuations(command)

        # Re-parse and check expanded version
        from .guardrails import _check_destructive_tokens

        try:
            import shlex

            parts = shlex.split(expanded)
            result = _check_destructive_tokens(parts)
            if result.action == GuardrailAction.DENY:
                return result
        except ValueError:
            # shlex parse error - might be intentional obfuscation
            return GuardrailResult(
                GuardrailAction.DENY, reason="Malformed heredoc or line continuation detected"
            )

    # Check for line continuation attempts
    if ShellCommandHardener.detect_line_continuation(command):
        expanded = ShellCommandHardener.expand_line_continuations(command)

        from .guardrails import _check_destructive_tokens

        try:
            import shlex

            parts = shlex.split(expanded)
            result = _check_destructive_tokens(parts)
            if result.action == GuardrailAction.DENY:
                return result
        except ValueError:
            return GuardrailResult(
                GuardrailAction.DENY, reason="Malformed line continuation detected"
            )

    return GuardrailResult(GuardrailAction.ALLOW)


def check_mcp_server_safety(
    server_spec: dict[str, Any], security_level: SecurityLevel = SecurityLevel.BALANCED
) -> GuardrailResult:
    """Validate MCP server configuration for safety.

    Args:
        server_spec: MCP server specification dict
        security_level: Security hardening level

    Returns:
        GuardrailResult denying if unsafe configuration detected
    """
    is_valid, reason = MCPServerValidator.validate_server_config(server_spec, security_level)

    if not is_valid:
        return GuardrailResult(
            GuardrailAction.DENY, reason=f"MCP server validation failed: {reason}"
        )

    return GuardrailResult(GuardrailAction.ALLOW)


def create_pre_execution_guardrail_hardened() -> Callable[
    [Tool, dict[str, Any], MemoryStore], GuardrailResult
]:
    """Create a comprehensive pre-execution guardrail that includes hardening checks.

    Returns:
        Function suitable for use as a pre-execution guardrail rule
    """

    def hardened_pre_check(tool: Tool, args: dict[str, Any], store: MemoryStore) -> GuardrailResult:
        """Comprehensive pre-execution guardrail with hardening.

        Args:
            tool: Tool being executed
            args: Tool arguments
            store: Memory store

        Returns:
            GuardrailResult allowing or denying execution
        """
        # First check: is run_command allowed at all?
        result = _block_run_command_if_not_allowed(tool, args, store)
        if result.action == GuardrailAction.DENY:
            return result

        # Environment integrity check
        result = check_environment_integrity()
        if result.action == GuardrailAction.DENY:
            return result

        # Config integrity check
        result = check_config_integrity()
        if result.action == GuardrailAction.DENY:
            return result

        # Enhanced path checks for read_file and ingest_document
        if tool.name in ("read_file", "ingest_document"):
            path = args.get("path", "")
            if isinstance(path, str):
                result = check_enhanced_path_safety(path)
                if result.action == GuardrailAction.DENY:
                    return result

                result = check_symlink_safety(path)
                if result.action == GuardrailAction.DENY:
                    return result

        # Enhanced shell command checks
        if tool.name == "run_command":
            command = args.get("command", "")
            if isinstance(command, str):
                result = check_shell_command_hardened(command)
                if result.action == GuardrailAction.DENY:
                    return result

        # Run the default guardrail policy
        return DEFAULT_POLICY.check_pre_execution(tool, args, store)

    return hardened_pre_check
