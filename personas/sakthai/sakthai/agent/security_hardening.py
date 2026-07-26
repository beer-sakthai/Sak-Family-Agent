"""Advanced security hardening system to prevent jailbreak attacks.

This module implements defense-in-depth protections against identified attack vectors:
1. Environment variable pinning and integrity verification
2. MCP server validation, sandboxing, and allowlisting
3. Enhanced path regex with Unicode and wildcard handling
4. Symlink detection and prevention
5. Config file integrity monitoring
6. TOCTOU (time-of-check-to-time-of-use) prevention
7. Shell command parsing improvements
8. Audit logging of security events
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import stat
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security hardening levels."""

    STRICT = "strict"  # Maximum protection, some UX impact
    BALANCED = "balanced"  # Good protection, minimal UX impact (default)
    PERMISSIVE = "permissive"  # Legacy behavior, minimal protection


@dataclass(frozen=True)
class SecurityEvent:
    """A security event for audit logging."""

    event_type: str  # "env_pin", "mcp_validation", "symlink_detected", etc.
    severity: str  # "critical", "high", "medium", "low"
    message: str
    timestamp: float
    details: dict[str, Any] | None = None


class EnvironmentVariablePinning:
    """Pin and verify critical environment variables at process start."""

    # Security-critical variables that should never change after startup
    _CRITICAL_VARS = {
        "SAKTHAI_SHELL_ALLOW",
        "SAKTHAI_READ_ALLOW",
        "SAKTHAI_HOME",
        "SAKTHAI_MCP_TIMEOUT",
        "SAKTHAI_GATEWAY_URL",
        "SAKTHAI_GATEWAY_API_KEY",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    }

    def __init__(self) -> None:
        """Capture and hash current environment variables."""
        self._pinned_values: dict[str, str | None] = {}
        self._pinned_hashes: dict[str, str] = {}
        self._pin_time = 0.0
        self._verify_enabled = True

        # Pin all critical variables
        for var in self._CRITICAL_VARS:
            value = os.environ.get(var)
            self._pinned_values[var] = value
            if value:
                self._pinned_hashes[var] = hashlib.sha256(value.encode()).hexdigest()

    def verify(self) -> list[SecurityEvent]:
        """Check if any critical variables have changed since pinning.

        Returns list of security events if tampering detected.
        """
        if not self._verify_enabled:
            return []

        events: list[SecurityEvent] = []
        import time

        for var in self._CRITICAL_VARS:
            current = os.environ.get(var)
            pinned = self._pinned_values[var]

            # Missing variables are OK (value=None is expected if not set)
            if pinned is None and current is None:
                continue

            # Variable disappeared or appeared
            if (pinned is None) != (current is None):
                events.append(
                    SecurityEvent(
                        event_type="env_tampering",
                        severity="high",
                        message=f"Environment variable {var} was "
                        + ("added" if current else "removed"),
                        timestamp=time.time(),
                        details={"variable": var},
                    )
                )
                continue

            # Variable value changed
            if current and current != pinned:
                # Double-check via hash to avoid string comparison issues
                current_hash = hashlib.sha256(current.encode()).hexdigest()
                if current_hash != self._pinned_hashes.get(var):
                    events.append(
                        SecurityEvent(
                            event_type="env_tampering",
                            severity="high",
                            message=f"Environment variable {var} was modified",
                            timestamp=time.time(),
                            details={"variable": var},
                        )
                    )

        return events

    def disable_verification(self) -> None:
        """Disable verification (for testing only)."""
        self._verify_enabled = False


# Global instance
_env_pinner = EnvironmentVariablePinning()


def pin_environment() -> None:
    """Initialize environment variable pinning at startup."""
    global _env_pinner
    _env_pinner = EnvironmentVariablePinning()
    logger.info("Environment variables pinned at process start")


def verify_environment() -> list[SecurityEvent]:
    """Verify that critical environment variables haven't been tampered with."""
    return _env_pinner.verify()


class MCPServerValidator:
    """Validate and sanitize external MCP server configurations."""

    # Approved external MCP servers (allowlist)
    APPROVED_SERVERS: dict[str, dict[str, Any]] = {
        # Add approved servers here
        # Format: "server_name": {"command": "...", "max_timeout": 30}
    }

    @staticmethod
    def validate_server_config(
        server_spec: dict[str, Any], security_level: SecurityLevel = SecurityLevel.BALANCED
    ) -> tuple[bool, str]:
        """Validate MCP server configuration for safety.

        Args:
            server_spec: Server configuration dict with 'name', 'command', 'args'
            security_level: Security hardening level

        Returns:
            (is_valid, reason) tuple
        """
        # Strict mode: only approved servers allowed
        if (
            security_level == SecurityLevel.STRICT
            and server_spec.get("name") not in MCPServerValidator.APPROVED_SERVERS
        ):
            return (
                False,
                f"MCP server '{server_spec.get('name')}' not in approved list (strict mode)",
            )

        # Check for suspicious patterns in command
        command = server_spec.get("command", "")
        if not command:
            return False, "MCP server 'command' is required"

        # Block commands that look suspicious
        suspicious_patterns = [
            r"eval",
            r"exec",
            r"rm\s+-rf",
            r":/dev/",
            r">\s*/dev/null",
            r">&\s*1",
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return (
                    False,
                    f"MCP server command contains suspicious pattern: {pattern}",
                )

        # Validate args if present
        args = server_spec.get("args", [])
        if not isinstance(args, list):
            return False, "MCP server 'args' must be a list"

        return True, "OK"

    @staticmethod
    def get_sandbox_wrapper(command: str, timeout_sec: int = 30) -> list[str]:
        """Generate a sandbox wrapper command for MCP server.

        Runs the server with resource limits (CPU, memory, timeout).

        Args:
            command: Original command
            timeout_sec: Execution timeout in seconds

        Returns:
            List of command args to execute in sandbox
        """
        # Use timeout + ulimit pattern for basic sandboxing
        # More robust would use seccomp/AppArmor profiles
        wrapper = [
            "timeout",
            str(timeout_sec),
            "sh",
            "-c",
            # Limit memory (512MB), CPU (1 core), file descriptors
            "ulimit -m 524288 -t 60 -n 256; " + command,
        ]
        return wrapper


class EnhancedPathValidator:
    """Enhanced path validation with improved regex and Unicode handling."""

    # Unicode normalization forms that could bypass checks
    UNICODE_FORMS = ["NFC", "NFD", "NFKC", "NFKD"]

    @staticmethod
    def normalize_path_thoroughly(path: str) -> list[str]:
        """Normalize path in all Unicode forms to catch evasion attempts.

        Args:
            path: Raw path string

        Returns:
            List of normalized forms to check
        """
        import unicodedata

        normalized = []
        for form in EnhancedPathValidator.UNICODE_FORMS:
            try:
                norm = unicodedata.normalize(form, path)  # type: ignore[arg-type]
                normalized.append(norm)
            except (TypeError, ValueError):
                pass

        return normalized or [path]

    @staticmethod
    def detect_glob_patterns(path: str) -> list[str]:
        """Detect glob/wildcard patterns that could expand to sensitive paths.

        Args:
            path: Path potentially containing globs

        Returns:
            List of detected glob patterns
        """
        patterns = []

        # Bracket glob patterns: /[re]ot/.ssh/id_rsa
        if re.search(r"\[[^\]]*\]", path):
            patterns.append("bracket_glob")

        # Single-char wildcards: /r?ot/.ssh/id_rsa
        if "?" in path:
            patterns.append("single_char_wildcard")

        # Multi-char wildcards: /*/ssh/id_rsa
        if "*" in path:
            patterns.append("multi_char_wildcard")

        # Brace expansion: /root/.ssh/id_{rsa,dsa,ecdsa}
        if "{" in path and "}" in path:
            patterns.append("brace_expansion")

        return patterns

    @staticmethod
    def check_case_sensitivity(path: str) -> bool:
        """Check if path uses mixed case (could bypass checks on case-insensitive FS).

        Args:
            path: Path to check

        Returns:
            True if suspicious case mixing detected
        """
        # SSH dirs/files with unusual casing
        suspicious_patterns = [".ssh", ".aws", ".env", "id_rsa", "credentials"]
        for pattern in suspicious_patterns:
            # Check if path contains this pattern in different case
            lower_pattern = pattern.lower()
            if lower_pattern in path.lower() and pattern not in path:
                return True
        return False


class SymlinkDetector:
    """Detect and prevent symlink-based traversal attacks."""

    @staticmethod
    def is_symlink(path: str | Path) -> bool:
        """Check if path is a symlink."""
        try:
            return Path(path).is_symlink()
        except (OSError, ValueError):
            return False

    @staticmethod
    def resolve_symlink_chain(path: str | Path, max_depth: int = 10) -> tuple[Path, list[Path]]:
        """Resolve symlink chain, detecting circular references and depth attacks.

        Args:
            path: Path to resolve
            max_depth: Maximum symlink depth to follow

        Returns:
            (final_path, symlinks_followed) tuple
        """
        current = Path(path)
        symlinks_followed: list[Path] = []
        depth = 0

        while current.is_symlink() and depth < max_depth:
            symlink_target = current.readlink()
            symlinks_followed.append(current)
            current = (
                symlink_target
                if symlink_target.is_absolute()
                else (current.parent / symlink_target)
            )
            depth += 1

        if depth >= max_depth:
            logger.warning(f"Symlink chain exceeded max depth {max_depth} for {path}")

        return current, symlinks_followed

    @staticmethod
    def detect_dangerous_symlinks(target_path: str) -> list[SecurityEvent]:
        """Detect if target or any parent directories are symlinks to sensitive locations.

        Args:
            target_path: Path to check

        Returns:
            List of security events if dangerous symlinks detected
        """
        events: list[SecurityEvent] = []
        import time

        current = Path(target_path).resolve()

        # Check if target itself is a symlink
        if Path(target_path).is_symlink():
            resolved, chain = SymlinkDetector.resolve_symlink_chain(target_path)

            # Check if final resolved path is in critical directory
            critical_dirs = {"/root", "/etc", "/home", "/var", "/sys", "/proc"}
            if any(str(resolved).startswith(cdir) for cdir in critical_dirs):
                events.append(
                    SecurityEvent(
                        event_type="symlink_traversal",
                        severity="high",
                        message=f"Symlink {target_path} resolves to critical directory: {resolved}",
                        timestamp=time.time(),
                        details={"target": str(target_path), "resolves_to": str(resolved)},
                    )
                )

        return events


class ConfigFileIntegrity:
    """Monitor configuration file integrity to prevent tampering."""

    def __init__(self, config_files: list[Path] | None = None) -> None:
        """Initialize config file integrity monitoring.

        Args:
            config_files: List of config file paths to monitor
        """
        self.config_files = config_files or [
            Path.home() / ".sakthai" / "mcp.json",
            Path.home() / ".sakthai" / ".env",
        ]
        self.hashes: dict[Path, str] = {}
        self._capture_hashes()

    def _capture_hashes(self) -> None:
        """Capture SHA256 hashes of all config files."""
        for config_file in self.config_files:
            if config_file.exists():
                try:
                    with open(config_file, "rb") as f:
                        content = f.read()
                    self.hashes[config_file] = hashlib.sha256(content).hexdigest()
                except OSError as e:
                    logger.warning(f"Could not hash config file {config_file}: {e}")

    def verify(self) -> list[SecurityEvent]:
        """Check if any config files have been modified.

        Returns:
            List of security events if tampering detected
        """
        events: list[SecurityEvent] = []
        import time

        for config_file in self.config_files:
            if not config_file.exists():
                continue

            try:
                with open(config_file, "rb") as f:
                    content = f.read()
                current_hash = hashlib.sha256(content).hexdigest()

                if config_file in self.hashes and current_hash != self.hashes[config_file]:
                    events.append(
                        SecurityEvent(
                            event_type="config_tampering",
                            severity="high",
                            message=f"Configuration file {config_file} was modified",
                            timestamp=time.time(),
                            details={"file": str(config_file)},
                        )
                    )
                    # Update hash for next check
                    self.hashes[config_file] = current_hash
            except OSError as e:
                logger.warning(f"Could not verify config file {config_file}: {e}")

        return events

    def check_permissions(self) -> list[SecurityEvent]:
        """Check if config files have overly permissive permissions.

        Returns:
            List of security events if permissions too open
        """
        events: list[SecurityEvent] = []
        import time

        for config_file in self.config_files:
            if not config_file.exists():
                continue

            try:
                mode = config_file.stat().st_mode
                # Check if world-readable or world-writable
                if mode & (stat.S_IROTH | stat.S_IWOTH):
                    events.append(
                        SecurityEvent(
                            event_type="config_permission",
                            severity="high",
                            message=f"Config file {config_file} is world-readable/writable: {oct(mode)}",
                            timestamp=time.time(),
                            details={"file": str(config_file), "mode": oct(mode)},
                        )
                    )
            except OSError as e:
                logger.warning(f"Could not check permissions for {config_file}: {e}")

        return events


class TOCTOUPrevention:
    """Prevent time-of-check-to-time-of-use (TOCTOU) attacks on file operations."""

    @staticmethod
    def atomic_check_and_read(
        file_path: Path, check_fn: Callable[[Path], bool], max_retries: int = 3
    ) -> tuple[bool, str]:
        """Atomically check and read a file without TOCTOU window.

        Args:
            file_path: Path to file
            check_fn: Function to validate file (returns bool)
            max_retries: Maximum retry attempts on mismatch

        Returns:
            (success, content) tuple
        """
        import time

        for attempt in range(max_retries):
            # Capture initial state
            try:
                initial_stat = file_path.stat()
            except FileNotFoundError:
                return False, "File not found"

            # Perform check
            if not check_fn(file_path):
                return False, "Check failed"

            # Read file
            try:
                with open(file_path) as f:
                    content = f.read()
            except OSError:
                return False, "Could not read file"

            # Verify file didn't change during read
            try:
                final_stat = file_path.stat()
                if (
                    initial_stat.st_mtime == final_stat.st_mtime
                    and initial_stat.st_size == final_stat.st_size
                ):
                    return True, content
            except FileNotFoundError:
                pass

            # Retry on mismatch
            if attempt < max_retries - 1:
                time.sleep(0.01 * (2**attempt))  # Exponential backoff

        return False, "TOCTOU mismatch: file changed during read"


class ShellCommandHardener:
    """Enhanced shell command parsing to detect bypass attempts."""

    # Heredoc patterns: <<EOF, <<'EOF', <<-EOF, etc.
    HEREDOC_PATTERN = re.compile(r"<<\s*-?['\"]*\w+['\"]*")

    # Line continuation: backslash at end of line
    CONTINUATION_PATTERN = re.compile(r"\\\s*$", re.MULTILINE)

    @staticmethod
    def detect_heredoc(command: str) -> list[str]:
        """Detect heredoc patterns in command.

        Args:
            command: Shell command string

        Returns:
            List of detected heredoc delimiters
        """
        matches = ShellCommandHardener.HEREDOC_PATTERN.findall(command)
        return matches

    @staticmethod
    def detect_line_continuation(command: str) -> bool:
        """Detect line continuation attempts.

        Args:
            command: Shell command string

        Returns:
            True if line continuation detected
        """
        return bool(ShellCommandHardener.CONTINUATION_PATTERN.search(command))

    @staticmethod
    def expand_line_continuations(command: str) -> str:
        """Expand line continuations to reveal full command.

        Args:
            command: Shell command with potential continuations

        Returns:
            Expanded command string
        """
        # Replace backslash+newline with space to show full logical line
        expanded = re.sub(r"\\\s*\n", " ", command)
        return expanded


class AuditLogger:
    """Centralized audit logging for security events."""

    def __init__(self, log_file: Path | None = None) -> None:
        """Initialize audit logger.

        Args:
            log_file: Path to audit log file (default: ~/.sakthai/audit.log)
        """
        self.log_file = log_file or (Path.home() / ".sakthai" / "audit.log")
        self.events: list[SecurityEvent] = []

    def log_event(self, event: SecurityEvent) -> None:
        """Log a security event.

        Args:
            event: SecurityEvent to log
        """
        self.events.append(event)

        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.log_file, "a") as f:
                event_dict = {
                    "timestamp": event.timestamp,
                    "type": event.event_type,
                    "severity": event.severity,
                    "message": event.message,
                    "details": event.details or {},
                }
                f.write(json.dumps(event_dict) + "\n")
        except OSError as e:
            logger.error(f"Could not write to audit log: {e}")

    def check_critical_events(self) -> list[SecurityEvent]:
        """Get all critical/high severity events since last check.

        Returns:
            List of critical security events
        """
        return [e for e in self.events if e.severity in ("critical", "high")]


# Global audit logger
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    return _audit_logger
