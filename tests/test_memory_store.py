"""Tests for the MemoryStore public API and snapshot helpers."""

from __future__ import annotations

import sqlite3

import pytest

from sakthai.memory.store import (SNAPSHOT_VERSION, Fact, MemoryStore,
                                  Observation, snapshot_to_csv,
                                  snapshot_to_jsonl)


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


# -- list_facts date range filtering ------------------------------------


def test_list_facts_date_range(store: MemoryStore) -> None:
    import time

    t0 = int(time.time()) - 100
    fid_old = store.add_fact("old fact")
    # Manually backdate created_at so we have a fact clearly before `t_mid`.
    store._conn.execute("UPDATE facts SET created_at = ? WHERE id = ?", (t0, fid_old))
    store._conn.commit()

    t_mid = int(time.time()) - 50
    fid_new = store.add_fact("new fact")

    # after_ts: only the new fact falls at or after t_mid
    recent = store.list_facts(after_ts=t_mid)
    assert len(recent) == 1
    assert recent[0].id == fid_new

    # before_ts: only the old fact falls at or before t_mid
    old_only = store.list_facts(before_ts=t_mid)
    assert len(old_only) == 1
    assert old_only[0].id == fid_old

    # both bounds: no fact falls in a 1-second window between the two
    empty = store.list_facts(after_ts=t_mid - 1, before_ts=t_mid - 1)
    assert empty == []

    # no bounds: both facts returned
    all_facts = store.list_facts()
    assert len(all_facts) == 2


# -- _encode_tags / _decode_tags edge cases ------------------------------


def test_encode_tags_invalid_type_raises() -> None:
    from sakthai.memory.store import _encode_tags

    with pytest.raises(ValueError, match="list of strings"):
        _encode_tags({"a": 1})  # type: ignore[arg-type]


def test_decode_tags_tolerates_junk() -> None:
    from sakthai.memory.store import _decode_tags

    assert _decode_tags("{not valid}") == []  # invalid JSON
    assert _decode_tags('{"k": "v"}') == []  # JSON object, not list
    assert _decode_tags(None) == []  # None input


# -- forget_fact ---------------------------------------------------------


def test_forget_fact_returns_true_and_removes_row(store: MemoryStore) -> None:
    fid = store.add_fact("to be deleted")
    assert store.forget_fact(fid) is True
    assert store.list_facts() == []


def test_forget_fact_missing_id_returns_false(store: MemoryStore) -> None:
    assert store.forget_fact(999) is False


def test_forget_fact_does_not_affect_siblings(store: MemoryStore) -> None:
    fid_keep = store.add_fact("survivor")
    fid_del = store.add_fact("doomed")
    store.forget_fact(fid_del)
    remaining = store.list_facts()
    assert len(remaining) == 1
    assert remaining[0].id == fid_keep


def test_forget_fact_is_idempotent(store: MemoryStore) -> None:
    fid = store.add_fact("ephemeral")
    assert store.forget_fact(fid) is True
    assert store.forget_fact(fid) is False  # already gone


# -- _encode_tags edge cases ---------------------------------------------


def test_encode_tags_all_whitespace_returns_none() -> None:
    from sakthai.memory.store import _encode_tags

    assert _encode_tags(["  ", "\t", ""]) is None


def test_encode_tags_none_input_returns_none() -> None:
    from sakthai.memory.store import _encode_tags

    assert _encode_tags(None) is None


# -- _validate_row error paths -------------------------------------------


def test_validate_row_non_dict_raises() -> None:
    from sakthai.memory.store import _validate_row

    with pytest.raises(ValueError, match="must be a dict"):
        _validate_row(["not", "a", "dict"], {"value"}, "fact")


def test_validate_row_missing_fields_raises() -> None:
    from sakthai.memory.store import _validate_row

    with pytest.raises(ValueError, match="missing fields"):
        _validate_row({"id": 1}, {"id", "value", "kind"}, "fact")


# -- import_from_dict validation paths -----------------------------------


def test_import_rejects_non_list_facts(store: MemoryStore) -> None:
    from sakthai.memory.store import SNAPSHOT_VERSION

    with pytest.raises(ValueError, match="list"):
        store.import_from_dict(
            {"version": SNAPSHOT_VERSION, "facts": "not a list", "observations": []}
        )


def test_import_rejects_fact_missing_required_field(store: MemoryStore) -> None:
    from sakthai.memory.store import SNAPSHOT_VERSION

    with pytest.raises(ValueError, match="missing fields"):
        store.import_from_dict(
            {
                "version": SNAPSHOT_VERSION,
                "facts": [{"id": 1}],  # missing kind, value, etc.
                "observations": [],
            }
        )


# -- rollback paths (injected SQLite failures) ---------------------------
#
# sqlite3.Connection methods are C-level and cannot be monkeypatched directly.
# Instead we verify the rollback contract behaviourally: an exception inside a
# transaction must leave the DB unchanged.


def test_update_fact_rolls_back_on_error(tmp_path: pytest.TempPathFactory) -> None:
    import sqlite3
    from pathlib import Path

    db = Path(str(tmp_path)) / "rollback.db"
    store = MemoryStore(db)
    try:
        fid = store.add_fact("original")
        # Corrupt the connection by closing it before the update to force an error.
        store._conn.close()
        with pytest.raises(sqlite3.ProgrammingError):
            store.update_fact(fid, "new value")
    finally:
        # Re-open to confirm the value was not changed.
        store2 = MemoryStore(db)
        try:
            facts = store2.list_facts()
            assert any(f.value == "original" for f in facts)
        finally:
            store2.close()


def test_consolidate_facts_rolls_back_on_error(
    tmp_path: pytest.TempPathFactory,
) -> None:
    from pathlib import Path

    db = Path(str(tmp_path)) / "rollback2.db"
    store = MemoryStore(db)
    try:
        store.add_fact("old fact")
        store._conn.close()
        with pytest.raises(sqlite3.ProgrammingError):
            store.consolidate_facts(age_seconds=-1)
    finally:
        store2 = MemoryStore(db)
        try:
            assert len(store2.list_facts()) == 1  # fact still present
        finally:
            store2.close()


# ---------------------------------------------------------------------------
# Exception / rollback branches (uncovered by normal happy-path tests)
# ---------------------------------------------------------------------------


class _RaisingOnCommit:
    """Thin proxy for sqlite3.Connection that raises OperationalError on commit().

    sqlite3.Connection is a C extension whose methods are read-only, so
    patch.object cannot replace them directly. This proxy is swapped in for
    store._conn in tests that need to exercise exception-handling branches.
    """

    def __init__(self, real: sqlite3.Connection) -> None:
        object.__setattr__(self, "_real", real)

    def __getattr__(self, name: str) -> object:
        return getattr(object.__getattribute__(self, "_real"), name)

    def commit(self) -> None:
        raise sqlite3.OperationalError("simulated disk full")


class _RaisingOnExecute:
    """Proxy that replaces execute() return value with a configurable fetchall."""

    def __init__(self, real: sqlite3.Connection, fetchall_result: list) -> None:
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_fetchall_result", fetchall_result)

    def __getattr__(self, name: str) -> object:
        return getattr(object.__getattribute__(self, "_real"), name)

    def execute(self, *args: object, **kwargs: object) -> object:
        result = object.__getattribute__(self, "_fetchall_result")

        class _FakeResult:
            def fetchall(self) -> list:
                return result

        return _FakeResult()


def test_render_prompt_block_includes_keyed_facts(store: MemoryStore) -> None:
    store.add_fact("dark", kind="pref", key="theme")
    block = store.render_prompt_block()
    assert "theme: dark" in block


def test_healthcheck_unknown_on_empty_result(store: MemoryStore) -> None:
    real_conn = store._conn
    store._conn = _RaisingOnExecute(real_conn, [])  # type: ignore[assignment]
    try:
        assert store.healthcheck() == "unknown"
    finally:
        store._conn = real_conn


def test_healthcheck_reports_integrity_errors(store: MemoryStore) -> None:
    real_conn = store._conn
    store._conn = _RaisingOnExecute(real_conn, [("corruption on page 3",)])  # type: ignore[assignment]
    try:
        result = store.healthcheck()
        assert "corruption on page 3" in result
    finally:
        store._conn = real_conn


def test_migrate_schema_rollback_on_exception(store: MemoryStore) -> None:
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError, match="simulated disk full"):
            store._migrate_schema()
    finally:
        store._conn = real_conn


def test_update_fact_rollback_on_exception(store: MemoryStore) -> None:
    fid = store.add_fact("original")
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.update_fact(fid, "new value")
    finally:
        store._conn = real_conn


def test_consolidate_facts_rollback_on_exception(store: MemoryStore) -> None:
    store.add_fact("old fact")
    # age_seconds < 0 sets threshold in the future, so the just-added fact qualifies
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.consolidate_facts(age_seconds=-86400)
    finally:
        store._conn = real_conn


def test_deduplicate_facts_rollback_on_exception(store: MemoryStore) -> None:
    store.add_fact("val1", kind="pref", key="color")
    store.add_fact("val2", kind="pref", key="color")
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.deduplicate_facts()
    finally:
        store._conn = real_conn


def test_deduplicate_observations_rollback_on_exception(store: MemoryStore) -> None:
    store.add_observation("same summary")
    store.add_observation("same summary")
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.deduplicate_observations()
    finally:
        store._conn = real_conn


def test_import_snapshot_requires_dict(store: MemoryStore) -> None:
    with pytest.raises(ValueError, match="snapshot must be a dict"):
        store.import_from_dict("not a dict")  # type: ignore[arg-type]


def test_import_snapshot_rollback_on_exception(store: MemoryStore) -> None:
    store.add_fact("a fact")
    snapshot = store.export_to_dict()
    real_conn = store._conn
    store._conn = _RaisingOnCommit(real_conn)  # type: ignore[assignment]
    try:
        with pytest.raises(sqlite3.OperationalError):
            store.import_from_dict(snapshot, mode="merge")
    finally:
        store._conn = real_conn
