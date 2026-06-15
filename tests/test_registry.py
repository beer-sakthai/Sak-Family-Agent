"""Tests for the agent tool registry (sakthai/agent/registry.py)."""

from __future__ import annotations

from sakthai.agent.registry import ToolRegistry, builtin_registry
from sakthai.agent.tools import BUILTIN_TOOLS, Tool
from sakthai.memory.store import MemoryStore


def _tool(name: str, desc: str = "d") -> Tool:
    def _handler(args: dict, store: MemoryStore) -> str:
        return name

    return Tool(
        name=name,
        description=desc,
        input_schema={"type": "object", "properties": {}},
        handler=_handler,
    )


def test_builtin_registry_has_all_builtins() -> None:
    reg = builtin_registry()
    assert len(reg) == len(BUILTIN_TOOLS)
    assert "learn" in reg
    assert reg.get("learn") is not None


def test_get_missing_returns_none() -> None:
    assert builtin_registry().get("nope") is None


def test_schemas_match_tools_in_order() -> None:
    reg = ToolRegistry([_tool("a"), _tool("b")])
    assert [s["name"] for s in reg.schemas()] == ["a", "b"]
    assert [t.name for t in reg.tools] == ["a", "b"]


def test_with_tools_merges_and_overrides() -> None:
    base = ToolRegistry([_tool("a", "base-a"), _tool("b")])
    merged = base.with_tools([_tool("a", "new-a"), _tool("c")])
    assert set(merged.names()) == {"a", "b", "c"}
    assert merged.get("a").description == "new-a"  # later wins on a name clash
    # The base registry is left untouched.
    assert base.get("a").description == "base-a"
    assert "c" not in base


def test_duplicate_names_collapse_keeping_last() -> None:
    reg = ToolRegistry([_tool("x", "first"), _tool("x", "second")])
    assert len(reg) == 1
    assert reg.get("x").description == "second"
