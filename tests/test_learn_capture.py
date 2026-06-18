from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.learn.capture import learn
from sakthai.memory.store import MemoryStore


def test_learn_basic(sakthai_home: Path) -> None:
    """Test storing a simple fact."""
    fact_id = learn("The sky is blue")
    assert fact_id > 0

    with MemoryStore() as store:
        facts = store.list_facts()
        assert len(facts) == 1
        assert facts[0].value == "The sky is blue"
        assert facts[0].kind == "note"


def test_learn_with_metadata(sakthai_home: Path) -> None:
    """Test storing a fact with kind, key, and tags."""
    fact_id = learn("Yellow", kind="pref", key="color", tags=["primary", "bright"])
    assert fact_id > 0

    with MemoryStore() as store:
        facts = store.list_facts()
        assert len(facts) == 1
        f = facts[0]
        assert f.value == "Yellow"
        assert f.kind == "pref"
        assert f.key == "color"
        assert f.tags == ["primary", "bright"]


def test_learn_rejects_empty(sakthai_home: Path) -> None:
    """Test that empty facts are rejected."""
    with pytest.raises(ValueError, match="empty fact"):
        learn("")
    with pytest.raises(ValueError, match="empty fact"):
        learn("   ")


def test_learn_rejects_non_string(sakthai_home: Path) -> None:
    """Test that non-string inputs are rejected."""
    with pytest.raises(ValueError, match="empty fact"):
        learn(None)  # type: ignore
    with pytest.raises(ValueError, match="empty fact"):
        learn(123)  # type: ignore


def test_learn_strips_whitespace(sakthai_home: Path) -> None:
    """Test that whitespace is stripped from the fact value."""
    learn("  Extra spaces  ")
    with MemoryStore() as store:
        facts = store.list_facts()
        assert facts[0].value == "Extra spaces"
