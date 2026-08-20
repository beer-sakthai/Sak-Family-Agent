"""Security containment and AST argument validation for MCP Tool Execution."""

from __future__ import annotations

from typing import Any


class SecurityViolationError(Exception):
    """Raised when tool arguments violate deterministic security guardrails."""


def validate_tool_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate all arguments against control characters and path traversal."""
    for key, value in arguments.items():
        if isinstance(value, str):
            # Check ASCII control characters
            if any(ord(c) < 32 and c not in ("\n", "\r", "\t") or ord(c) == 127 for c in value):
                raise SecurityViolationError(f"Control character detected in argument '{key}'")

            # Check path traversal
            if (
                "../" in value
                or "..\\" in value
                or value.startswith("/etc")
                or value.startswith("/root")
            ):
                raise SecurityViolationError(
                    f"Path traversal detected in argument '{key}': {value}"
                )

        elif isinstance(value, dict):
            validate_tool_arguments(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str) and ("../" in item or any(ord(c) < 32 for c in item)):
                    raise SecurityViolationError(
                        f"Security anomaly detected in list argument '{key}'"
                    )

    return arguments
