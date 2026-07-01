"""Property-based invariants for :class:`MemoryStore` (Hypothesis).

The example-based suites in ``test_memory_store.py`` pin specific behaviours.
These tests instead assert *invariants* that must hold for arbitrary fact and
observation sets — the kind of round-trip / idempotence / monotonicity
properties that hand-picked examples tend to under-cover:

* export → import is lossless,
* the ``snapshot_to_*`` renderers don't drop rows,
* ``deduplicate_*`` is idempotent and actually removes all duplicates,
* ``consolidate_facts`` never grows the fact table.

Every example builds a fresh in-memory store, so the tests stay hermetic and
fast.
"""

from __future__ import annotations

import json
from typing import Any

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from sakthai.memory.store import MemoryStore, snapshot_to_csv, snapshot_to_jsonl

# -- strategies --------------------------------------------------------------

# Printable text avoids null bytes (SQLite TEXT rejects them) and keeps failures
# readable. The store rejects blank fact values / observation summaries, so the
# text must contain at least one non-whitespace character.
_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs", "Cc"), min_codepoint=32),
    min_size=1,
    max_size=40,
).filter(lambda s: s.strip())
_kinds = st.sampled_from(["note", "pref", "profile", "task", "skill"])
_keys = st.none() | _text


@st.composite
def _fact_inputs(draw: st.DrawFn) -> dict[str, Any]:
    return {
        "value": draw(_text),
        "kind": draw(_kinds),
        "key": draw(_keys),
    }


@st.composite
def _obs_inputs(draw: st.DrawFn) -> dict[str, Any]:
    return {
        "summary": draw(_text),
        "weight": draw(st.floats(min_value=0.0, max_value=1.0)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0)),
    }


def _populate(
    store: MemoryStore, facts: list[dict[str, Any]], obs: list[dict[str, Any]]
) -> None:
    for f in facts:
        store.add_fact(f["value"], kind=f["kind"], key=f["key"])
    for o in obs:
        store.add_observation(
            o["summary"], weight=o["weight"], confidence=o["confidence"]
        )


_NO_FIXTURE_CHECK = settings(
    max_examples=60,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)


# -- round-trip --------------------------------------------------------------


@_NO_FIXTURE_CHECK
@given(
    facts=st.lists(_fact_inputs(), max_size=12),
    obs=st.lists(_obs_inputs(), max_size=12),
)
def test_export_import_roundtrip_is_lossless(
    facts: list[dict[str, Any]], obs: list[dict[str, Any]]
) -> None:
    """import_from_dict(export_to_dict()) reproduces the snapshot exactly."""
    src = MemoryStore(":memory:")
    dst = MemoryStore(":memory:")
    try:
        _populate(src, facts, obs)
        snapshot = src.export_to_dict()

        n_facts, n_obs = dst.import_from_dict(snapshot, mode="replace")
        assert n_facts == len(facts)
        assert n_obs == len(obs)

        # The portable payload (rows, not the wall-clock/db_path header) matches.
        reexported = dst.export_to_dict()
        assert reexported["facts"] == snapshot["facts"]
        assert reexported["observations"] == snapshot["observations"]
    finally:
        src.close()
        dst.close()


@_NO_FIXTURE_CHECK
@given(
    facts=st.lists(_fact_inputs(), max_size=12),
    obs=st.lists(_obs_inputs(), max_size=12),
)
def test_snapshot_jsonl_has_one_row_per_record(
    facts: list[dict[str, Any]], obs: list[dict[str, Any]]
) -> None:
    """JSONL rendering emits exactly one parseable line per fact/observation."""
    store = MemoryStore(":memory:")
    try:
        _populate(store, facts, obs)
        snapshot = store.export_to_dict()
        text = snapshot_to_jsonl(snapshot)
        lines = [ln for ln in text.splitlines() if ln]
        assert len(lines) == len(facts) + len(obs)
        types = [json.loads(ln)["type"] for ln in lines]
        assert types.count("fact") == len(facts)
        assert types.count("observation") == len(obs)
    finally:
        store.close()


@_NO_FIXTURE_CHECK
@given(
    facts=st.lists(_fact_inputs(), max_size=12),
    obs=st.lists(_obs_inputs(), max_size=12),
)
def test_snapshot_csv_has_header_plus_one_row_each(
    facts: list[dict[str, Any]], obs: list[dict[str, Any]]
) -> None:
    """CSV rendering emits a header plus one record line per fact/observation."""
    store = MemoryStore(":memory:")
    try:
        _populate(store, facts, obs)
        csv_text = snapshot_to_csv(store.export_to_dict())
        # csv may quote embedded newlines, so count via the csv reader, not splitlines.
        import csv as _csv
        import io as _io

        rows = list(_csv.DictReader(_io.StringIO(csv_text)))
        assert len(rows) == len(facts) + len(obs)
        assert {r["type"] for r in rows} <= {"fact", "observation"}
    finally:
        store.close()


# -- idempotence -------------------------------------------------------------


@_NO_FIXTURE_CHECK
@given(facts=st.lists(_fact_inputs(), max_size=16))
def test_deduplicate_facts_is_idempotent(facts: list[dict[str, Any]]) -> None:
    """A second deduplicate pass removes nothing, and no duplicate group remains."""
    store = MemoryStore(":memory:")
    try:
        _populate(store, facts, [])
        store.deduplicate_facts()
        assert store.deduplicate_facts() == 0

        # No (kind, key) or (kind, value) group has more than one survivor.
        keyed: dict[tuple[str, str], int] = {}
        keyless: dict[tuple[str, str], int] = {}
        for f in store.list_facts(limit=10_000):
            if f.key is not None:
                keyed[(f.kind, f.key)] = keyed.get((f.kind, f.key), 0) + 1
            else:
                keyless[(f.kind, f.value)] = keyless.get((f.kind, f.value), 0) + 1
        assert all(c == 1 for c in keyed.values())
        assert all(c == 1 for c in keyless.values())
    finally:
        store.close()


@_NO_FIXTURE_CHECK
@given(obs=st.lists(_obs_inputs(), max_size=16))
def test_deduplicate_observations_is_idempotent(obs: list[dict[str, Any]]) -> None:
    """A second observation-dedup pass removes nothing."""
    store = MemoryStore(":memory:")
    try:
        _populate(store, [], obs)
        store.deduplicate_observations()
        assert store.deduplicate_observations() == 0
    finally:
        store.close()


# -- monotonicity ------------------------------------------------------------


@_NO_FIXTURE_CHECK
@given(facts=st.lists(_fact_inputs(), min_size=1, max_size=16))
def test_consolidate_never_grows_facts(facts: list[dict[str, Any]]) -> None:
    """Consolidation only ever shrinks the fact table and adds at most one summary.

    Uses a negative age window so every just-written fact qualifies; the folded
    values must all reappear inside the single summary observation it creates.
    """
    store = MemoryStore(":memory:")
    try:
        _populate(store, facts, [])
        before_facts = len(store.list_facts(limit=10_000))
        before_obs = store.stats()["observations"]["total"]

        folded = store.consolidate_facts(age_seconds=-1)

        after_facts = len(store.list_facts(limit=10_000))
        after_obs = store.stats()["observations"]["total"]

        assert folded == before_facts
        assert after_facts <= before_facts
        assert after_obs <= before_obs + 1
        if before_facts:
            assert after_facts == 0
            assert after_obs == before_obs + 1
    finally:
        store.close()
