"""A tool registry: hold built-in and runtime-discovered tools by name.

The agent loop and the MCP server both operate on a set of :class:`Tool`
objects. A ``ToolRegistry`` keys them by name so the loop can dispatch a model's
tool call, emit the model-facing schemas, and merge in tools discovered at
runtime (e.g. from an external MCP server) — on a name clash the later tool wins,
letting a plugin deliberately shadow a built-in.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from .tools import BUILTIN_TOOLS, Tool


class ToolRegistry:
    """An ordered, name-keyed set of tools the agent can call."""

    def __init__(self, tools: Iterable[Tool] = ()) -> None:
        self._tools: dict[str, Tool] = {}
        for tool in tools:
            self._tools[tool.name] = tool

    @property
    def tools(self) -> tuple[Tool, ...]:
        return tuple(self._tools.values())

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def schemas(self) -> list[dict[str, Any]]:
        """Model-facing tool definitions, in registration order."""
        return [tool.schema() for tool in self._tools.values()]

    def with_tools(self, extra: Iterable[Tool]) -> ToolRegistry:
        """Return a new registry with ``extra`` merged in (extra overrides)."""
        merged = ToolRegistry(self._tools.values())
        for tool in extra:
            merged._tools[tool.name] = tool
        return merged

    def validate_all(self) -> dict[str, list[str]]:
        """Validate all registered tools' schemas and metadata.

        Returns a dictionary mapping tool names to a list of validation errors (empty list if healthy).
        """
        report: dict[str, list[str]] = {}
        for tool in self._tools.values():
            errors: list[str] = []
            if not tool.name or not re.match(r"^[a-z][a-z0-9_]*$", tool.name):
                errors.append(f"Invalid tool name format {tool.name!r}; must be snake_case.")
            if not tool.description or len(tool.description.strip()) < 20:
                errors.append("Tool description must be actionable and at least 20 characters.")
            if not isinstance(tool.input_schema, dict) or tool.input_schema.get("type") != "object":
                errors.append("Tool input_schema must be an object with 'type': 'object'.")
            if not callable(tool.handler):
                errors.append("Tool handler must be a callable.")
            report[tool.name] = errors
        return report

    def to_dict(self) -> list[dict[str, Any]]:
        """Return a list of serialized tool metadata dictionaries."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "schema": t.input_schema,
                "required": t.input_schema.get("required", []),
                "properties_count": len(t.input_schema.get("properties", {})),
            }
            for t in self._tools.values()
        ]

    def stats(self) -> dict[str, Any]:
        """Return diagnostic metrics for the registry."""
        total = len(self._tools)
        report = self.validate_all()
        valid = sum(1 for errs in report.values() if not errs)
        return {
            "total_tools": total,
            "valid_tools": valid,
            "healthy": total > 0 and valid == total,
            "names": list(self._tools.keys()),
        }

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


def builtin_registry() -> ToolRegistry:
    """A registry seeded with the built-in tools."""
    return ToolRegistry(BUILTIN_TOOLS)
