"""Property-based invariants for :class:`MemoryStore` (Hypothesis)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from sakthai.memory.store import (
    MemoryStore,
    snapshot_to_csv,
    snapshot_to_jsonl,
)

# -- strategies --------------------------------------------------------------

@st.composite
def facts_strategy(draw: st.DrawFn):
    kind = draw(st.sampled_from(["note", "pref", "project"]))
    key = draw(st.text(min_size=1, max_size=20))
    value = draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ""))
    return {"kind": kind, "key": key, "value": value}

@st.composite
def observations_strategy(draw: st.DrawFn):
    summary = draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ""))
    weight = draw(st.floats(min_value=0.0, max_value=1.0))
    confidence = draw(st.floats(min_value=0.0, max_value=1.0))
    return {"summary": summary, "weight": weight, "confidence": confidence}

# -- tests -------------------------------------------------------------------

@settings(suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow])
@given(
    facts=st.lists(facts_strategy(), min_size=0, max_size=10),
    obs=st.lists(observations_strategy(), min_size=0, max_size=10),
)
def test_export_import_roundtrip(facts: list[dict[str, Any]], obs: list[dict[str, Any]], tmp_path_factory: pytest.TempPathFactory) -> None:
    db = tmp_path_factory.mktemp("data") / "memory.db"
    with MemoryStore(db) as store:
        for f in facts:
            store.add_fact(f["value"], kind=f["kind"], key=f["key"])
        for o in obs:
            store.add_observation(o["summary"], weight=o["weight"], confidence=o["confidence"])

        snapshot = store.export_to_dict()

    db2 = tmp_path_factory.mktemp("data2") / "memory.db"
    with MemoryStore(db2) as store2:
        store2.import_from_dict(snapshot, mode="replace")
        snapshot2 = store2.export_to_dict()

    assert snapshot["facts"] == snapshot2["facts"]
    assert snapshot["observations"] == snapshot2["observations"]
