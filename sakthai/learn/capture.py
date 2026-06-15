"""Record a single fact in memory: backs ``sakthai learn``."""

from __future__ import annotations

from ..memory.store import MemoryStore


def learn(
    value: str,
    *,
    kind: str = "note",
    key: str | None = None,
    tags: list[str] | None = None,
) -> int:
    """Store one fact and return its id. Opens and closes the store per call."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Cannot learn an empty fact.")
    with MemoryStore() as store:
        return store.add_fact(value.strip(), kind=kind, key=key, tags=tags)
