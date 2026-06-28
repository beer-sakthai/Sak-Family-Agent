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


def test_empty_registry_len_is_zero() -> None:
    reg = ToolRegistry()
    assert len(reg) == 0
    assert reg.tools == ()
    assert reg.names() == []
    assert reg.schemas() == []


def test_len_reflects_tool_count() -> None:
    reg = ToolRegistry([_tool("a"), _tool("b"), _tool("c")])
    assert len(reg) == 3


def test_contains_existing_and_missing() -> None:
    reg = ToolRegistry([_tool("present")])
    assert "present" in reg
    assert "absent" not in reg


def test_names_returns_ordered_list() -> None:
    reg = ToolRegistry([_tool("alpha"), _tool("beta"), _tool("gamma")])
    assert reg.names() == ["alpha", "beta", "gamma"]


def test_handler_dispatch_executes_and_returns_result() -> None:
    """get() followed by handler() must dispatch and return the tool's output."""
    with MemoryStore(":memory:") as store:
        reg = ToolRegistry([_tool("ping")])
        tool = reg.get("ping")
        assert tool is not None
        result = tool.handler({}, store)
        assert result == "ping"


def test_with_tools_does_not_mutate_base() -> None:
    base = ToolRegistry([_tool("a")])
    _ = base.with_tools([_tool("b")])
    assert "b" not in base
    assert len(base) == 1
