"""Tests for the small memory-adjacent helpers:

* ``memory.provider.SakThaiMemoryProvider`` — the system-prompt adapter.
* ``memory.backup.backup_memory`` — the timestamped DB copy.
* ``learn.capture.learn`` — the explicit single-fact write path.

All use the ``sakthai_home`` fixture so the default ``MemoryStore()`` (which
these helpers construct internally) lands in an isolated tmp database.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.config import memory_db_path
from sakthai.learn.capture import learn
from sakthai.memory import provider as provider_mod
from sakthai.memory.backup import backup_memory
from sakthai.memory.provider import SakThaiMemoryProvider
from sakthai.memory.store import MemoryStore

# -- provider ------------------------------------------------------------


def test_provider_static_surface(sakthai_home: Path) -> None:
    p = SakThaiMemoryProvider()
    assert p.name == "sakthai"
    assert p.is_available() is True
    assert p.get_tool_schemas() == []


def test_provider_block_empty_before_initialize(sakthai_home: Path) -> None:
    p = SakThaiMemoryProvider()
    assert p.system_prompt_block() == ""


def test_provider_renders_facts_after_initialize(sakthai_home: Path) -> None:
    with MemoryStore() as store:
        store.add_fact("the user prefers dark mode")
    p = SakThaiMemoryProvider()
    p.initialize()
    block = p.system_prompt_block()
    assert "dark mode" in block
    assert p.prefetch("anything") == block
    p.shutdown()
    assert p.system_prompt_block() == ""


def test_provider_initialize_degrades_gracefully(
    sakthai_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom() -> MemoryStore:
        raise RuntimeError("db unusable")

    monkeypatch.setattr(provider_mod, "MemoryStore", _boom)
    p = SakThaiMemoryProvider()
    p.initialize()  # must not raise
    assert p.system_prompt_block() == ""


# -- backup --------------------------------------------------------------


def test_backup_copies_database(sakthai_home: Path) -> None:
    with MemoryStore() as store:
        store.add_fact("remember me")
    db = memory_db_path()

    dest = backup_memory()

    assert dest.exists()
    assert dest.parent == db.parent
    assert dest.name.startswith("memory_")
    assert dest.name.endswith(".db.bak")
    assert dest.read_bytes() == db.read_bytes()


# -- learn (capture) -----------------------------------------------------


def test_learn_stores_and_returns_id(sakthai_home: Path) -> None:
    fact_id = learn("apples are red")
    assert isinstance(fact_id, int)
    with MemoryStore() as store:
        values = [f.value for f in store.list_facts()]
    assert "apples are red" in values


def test_learn_strips_whitespace(sakthai_home: Path) -> None:
    learn("   trimmed   ")
    with MemoryStore() as store:
        values = [f.value for f in store.list_facts()]
    assert "trimmed" in values


def test_learn_passes_kind_key_tags(sakthai_home: Path) -> None:
    learn("x", kind="pref", key="theme", tags=["ui"])
    with MemoryStore() as store:
        fact = store.get_fact_by_key("pref", "theme")
    assert fact is not None
    assert fact.value == "x"
    assert fact.tags == ["ui"]


@pytest.mark.parametrize("bad", ["", "   ", "\n\t"])
def test_learn_rejects_empty(sakthai_home: Path, bad: str) -> None:
    with pytest.raises(ValueError):
        learn(bad)


def test_learn_rejects_non_string(sakthai_home: Path) -> None:
    with pytest.raises(ValueError):
        learn(123)  # type: ignore[arg-type]
