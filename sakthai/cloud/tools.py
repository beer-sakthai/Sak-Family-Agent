"""Memory tools exposed to the cloud (ADK) runtime.

These are plain, typed Python callables — the shape Google ADK expects for
function tools, with the docstring and signature doubling as the model-facing
schema. Each one opens a :class:`MemoryStore` and goes through it, so the cloud
agent shares the same persistence seam as the local agent loop and MCP server.

They are deliberately separate from ``agent/tools.py``'s JSON-schema ``Tool``
objects: ADK wants native functions, not the ``(args, store) -> str`` handler
shape. The behaviour is the same; only the calling convention differs.
"""

from __future__ import annotations

from collections.abc import Callable

from ..memory.store import MemoryStore

_RECALL_LIMIT_MAX = 200


def _clamp(limit: int, default: int) -> int:
    if limit <= 0:
        return default
    return min(limit, _RECALL_LIMIT_MAX)


def learn_fact(value: str, kind: str = "note", key: str = "") -> str:
    """Save a single fact to persistent memory.

    Args:
        value: The fact to remember (free text).
        kind: A short category label, e.g. ``note``, ``preference``, ``finding``.
        key: An optional stable identifier for the fact.

    Returns:
        A confirmation string including the new fact id.
    """
    with MemoryStore() as store:
        fact_id = store.add_fact(value, kind=kind, key=key or None)
    return f"Saved fact #{fact_id} [{kind}]."


def recall_memory(limit: int = 20) -> str:
    """List the most recent facts and top observations from memory.

    Args:
        limit: Maximum number of facts to return (1–200).

    Returns:
        A newline-separated rendering of facts and observations.
    """
    capped = _clamp(limit, 20)
    with MemoryStore() as store:
        facts = store.list_facts(limit=capped)
        observations = store.top_observations(limit=10)
    lines = [f"#{f.id} [{f.kind}] {f.value}" for f in facts]
    lines += [f"~ ({o.weight:.2f}) {o.summary}" for o in observations]
    return "\n".join(lines) if lines else "Memory is empty."


def search_memory(query: str, limit: int = 50) -> str:
    """Full-text search facts and observations.

    Args:
        query: The text to search for.
        limit: Maximum number of facts to return (1–200).

    Returns:
        A newline-separated rendering of matching facts and observations.
    """
    capped = _clamp(limit, 50)
    with MemoryStore() as store:
        facts, observations = store.search_memory(query, limit=capped)
    lines = [f"#{f.id} [{f.kind}] {f.value}" for f in facts]
    lines += [f"~ ({o.weight:.2f}) {o.summary}" for o in observations]
    return "\n".join(lines) if lines else f"No matches for {query!r}."


def forget_fact(fact_id: int) -> str:
    """Delete a fact by its numeric id.

    Args:
        fact_id: The id of the fact to remove.

    Returns:
        A confirmation string indicating whether the fact existed.
    """
    with MemoryStore() as store:
        removed = store.forget_fact(fact_id)
    return f"Forgot fact #{fact_id}." if removed else f"No fact #{fact_id} found."


# The function set wired into the cloud agent. Mirrors the read/write memory
# surface of the local runtimes; ordered learn → recall → search → forget.
MEMORY_TOOL_FUNCTIONS: tuple[Callable[..., str], ...] = (
    learn_fact,
    recall_memory,
    search_memory,
    forget_fact,
)

__all__ = [
    "MEMORY_TOOL_FUNCTIONS",
    "forget_fact",
    "learn_fact",
    "recall_memory",
    "search_memory",
]
