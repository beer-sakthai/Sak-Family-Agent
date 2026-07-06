"""A tool registry: hold built-in and runtime-discovered tools by name.

The agent loop and the MCP server both operate on a set of :class:`Tool`
objects. A ``ToolRegistry`` keys them by name so the loop can dispatch a model's
tool call, emit the model-facing schemas, and merge in tools discovered at
runtime (e.g. from an external MCP server) — on a name clash the later tool wins,
letting a plugin deliberately shadow a built-in.
"""

from __future__ import annotations

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

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: object) -> bool:
        return name in self._tools


def builtin_registry() -> ToolRegistry:
    """A registry seeded with the built-in tools."""
    return ToolRegistry(BUILTIN_TOOLS)
