"""Shared fixtures: an isolated memory store and a sandboxed SAKTHAI_HOME."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _api_key_hash_secret() -> Iterator[None]:
    # billing.models.hash_api_key needs SAKTHAI_API_KEY_HASH_SECRET at runtime;
    # a deterministic per-suite value keeps the billing tests hermetic without
    # each one having to set it.
    previous = os.environ.get("SAKTHAI_API_KEY_HASH_SECRET")
    os.environ["SAKTHAI_API_KEY_HASH_SECRET"] = "test-hash-secret-do-not-use-in-prod"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("SAKTHAI_API_KEY_HASH_SECRET", None)
        else:
            os.environ["SAKTHAI_API_KEY_HASH_SECRET"] = previous


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
