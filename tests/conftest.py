"""Shared fixtures: an isolated memory store and a sandboxed SAKTHAI_HOME."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from sakthai.memory.store import MemoryStore


@pytest.fixture
def store(tmp_path: Path) -> Iterator[MemoryStore]:
    s = MemoryStore(tmp_path / "memory.db")
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def sakthai_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    # persona_memory_db_path()/FamilyMemoryView read Path.home() directly (by
    # design, so they resolve every persona's shard independent of whichever
    # single persona the current process's SAKTHAI_HOME happens to be scoped
    # to) — patch it too so this fixture gives full isolation from the real
    # user home, not just from SAKTHAI_HOME-based paths.
    monkeypatch.setattr(Path, "home", lambda: home)
    return home
