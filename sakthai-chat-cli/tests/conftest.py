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
    return home
