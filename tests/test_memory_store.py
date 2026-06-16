"""Tests for the MemoryStore public API and snapshot helpers."""

from __future__ import annotations

import pytest

from sakthai.memory.store import (
    SNAPSHOT_VERSION,
    Fact,
    MemoryStore,
    Observation,
    snapshot_to_csv,
    snapshot_to_jsonl,
)


def test_add_and_list_facts(store: MemoryStore) -> None:
    fid = store.add_fact("likes tea", kind="pref", key="drink")
    assert isinstance(fid, int)
    facts = store.list_facts()
    assert len(facts) == 1
    assert facts[0].value == "likes tea"
    assert facts[0].kind == "pref"
    assert facts[0].key == "drink"


def test_healthcheck_ok(store: MemoryStore) -> None:
    assert store.healthcheck() == "ok"


def test_get_and_delete_by_key(store: MemoryStore) -> None:
    store.add_fact("dark", kind="pref", key="theme")
    assert store.get_fact_by_key("pref", "theme").value == "dark"
    assert store.delete_facts_by_key("pref", "theme") == 1
    assert store.get_fact_by_key("pref", "theme") is None


def test_tags_round_trip_and_search(store: MemoryStore) -> None:
    store.add_fact("ticket work", tags=["work", "work", " "])
    facts = store.search_by_tag("work")
    assert len(facts) == 1
    assert facts[0].tags == ["work"]  # de-duplicated, blanks dropped


def test_update_fact_requires_value(store: MemoryStore) -> None:
    fid = store.add_fact("first")
    assert store.update_fact(fid, "second") is True
    assert store.list_facts()[0].value == "second"
    assert store.update_fact(999, "missing") is False
    with pytest.raises(ValueError):
        store.update_fact(fid, "   ")


def test_observation_validation_and_ordering(store: MemoryStore) -> None:
    store.add_observation("low", weight=0.1)
    store.add_observation("high", weight=5.0)
    top = store.top_observations()
    assert [o.summary for o in top] == ["high", "low"]
    with pytest.raises(ValueError):
        store.add_observation("  ")


def test_search_memory_escapes_wildcards(store: MemoryStore) -> None:
    store.add_fact("100% sure")
    store.add_fact("nope")
    facts, _ = store.search_memory("100%")
    assert len(facts) == 1
    assert facts[0].value == "100% sure"


def test_render_prompt_block(store: MemoryStore) -> None:
    assert store.render_prompt_block() == ""
    store.add_fact("uses vim", kind="pref")
    store.add_observation("works late")
    block = store.render_prompt_block()
    assert "SakThai personal memory" in block
    assert "uses vim" in block
    assert "works late" in block


def test_deduplicate_facts(store: MemoryStore) -> None:
    store.add_fact("dark", kind="pref", key="theme")
    store.add_fact("light", kind="pref", key="theme")  # newer wins
    store.add_fact("solo")
    store.add_fact("solo")  # keyless dup by value
    removed = store.deduplicate_facts()
    assert removed == 2
    remaining = sorted(f.value for f in store.list_facts())
    assert remaining == ["light", "solo"]


def test_deduplicate_observations(store: MemoryStore) -> None:
    store.add_observation("dup", weight=1.0)
    store.add_observation("dup", weight=2.0)  # higher weight kept
    removed = store.deduplicate_observations()
    assert removed == 1
    assert store.top_observations()[0].weight == 2.0


def test_consolidate_facts(store: MemoryStore) -> None:
    store.add_fact("old fact")
    moved = store.consolidate_facts(age_seconds=-1)  # everything is "older"
    assert moved == 1
    assert store.list_facts() == []
    assert any("Consolidated" in o.summary for o in store.top_observations())


def test_stats(store: MemoryStore) -> None:
    store.add_fact("a", kind="note", tags=["x"])
    store.add_fact("b", kind="pref")
    store.add_observation("obs", weight=1.0, confidence=0.5)
    stats = store.stats()
    assert stats["facts"]["total"] == 2
    assert stats["facts"]["by_kind"] == {"note": 1, "pref": 1}
    assert stats["tags"] == {"x": 1}
    assert stats["observations"]["total"] == 1


def test_export_import_round_trip(tmp_path, store: MemoryStore) -> None:
    store.add_fact("keep me", kind="pref", key="k", tags=["t"])
    store.add_observation("watch this", weight=2.0)
    snapshot = store.export_to_dict()
    assert snapshot["version"] == SNAPSHOT_VERSION

    other = MemoryStore(tmp_path / "other.db")
    try:
        n_facts, n_obs = other.import_from_dict(snapshot, mode="replace")
        assert (n_facts, n_obs) == (1, 1)
        fact = other.list_facts()[0]
        assert fact.value == "keep me"
        assert fact.tags == ["t"]
    finally:
        other.close()


def test_import_rejects_bad_version(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        store.import_from_dict({"version": 999, "facts": [], "observations": []})


def test_import_rejects_bad_mode(store: MemoryStore) -> None:
    with pytest.raises(ValueError):
        store.import_from_dict(store.export_to_dict(), mode="nonsense")


def test_snapshot_to_jsonl_and_csv(store: MemoryStore) -> None:
    store.add_fact("f", tags=["a", "b"])
    store.add_observation("o")
    snap = store.export_to_dict()
    jsonl = snapshot_to_jsonl(snap)
    assert jsonl.count("\n") == 2
    assert '"type": "fact"' in jsonl

    csv_text = snapshot_to_csv(snap)
    assert csv_text.startswith("type,id,kind")
    assert "a,b" in csv_text  # tags flattened


def test_dataclasses_positional_construction() -> None:
    fact = Fact(1, "note", None, "v", None, 0, 0)
    assert fact.tags == []
    obs = Observation(1, "s", None, 1.0, 0.5, 0)
    assert obs.weight == 1.0


# -- forget_observation --------------------------------------------------


def test_forget_observation(store: MemoryStore) -> None:
    obs_id = store.add_observation("to be forgotten")
    assert store.forget_observation(obs_id) is True
    assert store.forget_observation(obs_id) is False  # already gone
    assert store.top_observations() == []


# -- import_from_dict merge mode -----------------------------------------


def test_import_merge_mode(tmp_path, store: MemoryStore) -> None:
    store.add_fact("original")
    snapshot = store.export_to_dict()

    other = MemoryStore(tmp_path / "other.db")
    try:
        other.add_fact("pre-existing")
        n_facts, n_obs = other.import_from_dict(snapshot, mode="merge")
        assert n_facts == 1
        assert n_obs == 0
        # Both the pre-existing fact and the imported one must survive.
        values = {f.value for f in other.list_facts()}
        assert "pre-existing" in values
        assert "original" in values
    finally:
        other.close()


# -- deduplicate dry_run / detailed flags --------------------------------


def test_deduplicate_facts_dry_run_does_not_delete(store: MemoryStore) -> None:
    store.add_fact("v1", kind="pref", key="color")
    store.add_fact("v2", kind="pref", key="color")
    count = store.deduplicate_facts(dry_run=True)
    assert count == 1
    assert len(store.list_facts()) == 2  # nothing actually deleted


def test_deduplicate_facts_detailed_returns_list(store: MemoryStore) -> None:
    fid1 = store.add_fact("old", kind="pref", key="theme")
    store.add_fact("new", kind="pref", key="theme")  # higher id wins
    result = store.deduplicate_facts(detailed=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].id == fid1  # older row is the one removed
    remaining = store.list_facts()
    assert len(remaining) == 1
    assert remaining[0].value == "new"


def test_deduplicate_observations_dry_run_does_not_delete(store: MemoryStore) -> None:
    store.add_observation("same text", weight=1.0)
    store.add_observation("same text", weight=2.0)
    count = store.deduplicate_observations(dry_run=True)
    assert count == 1
    assert len(store.top_observations()) == 2  # nothing deleted


def test_deduplicate_observations_detailed_returns_list(store: MemoryStore) -> None:
    store.add_observation("dup", weight=0.5)
    store.add_observation("dup", weight=1.5)  # higher weight kept
    result = store.deduplicate_observations(detailed=True)
    assert isinstance(result, list)
    assert len(result) == 1
    remaining = store.top_observations()
    assert len(remaining) == 1
    assert remaining[0].weight == 1.5


# -- update_fact tag paths -----------------------------------------------


def test_update_fact_sets_new_tags(store: MemoryStore) -> None:
    fid = store.add_fact("hello", tags=["old"])
    store.update_fact(fid, "hello", tags=["new"])
    assert store.list_facts()[0].tags == ["new"]


def test_update_fact_clears_tags_with_empty_list(store: MemoryStore) -> None:
    fid = store.add_fact("hello", tags=["a", "b"])
    store.update_fact(fid, "hello", tags=[])
    assert store.list_facts()[0].tags == []


# -- _encode_tags / _decode_tags edge cases ------------------------------


def test_encode_tags_invalid_type_raises() -> None:
    from sakthai.memory.store import _encode_tags

    with pytest.raises(ValueError, match="list of strings"):
        _encode_tags({"a": 1})  # type: ignore[arg-type]


def test_decode_tags_tolerates_junk() -> None:
    from sakthai.memory.store import _decode_tags

    assert _decode_tags("{not valid}") == []       # invalid JSON
    assert _decode_tags('{"k": "v"}') == []        # JSON object, not list
    assert _decode_tags(None) == []                # None input
