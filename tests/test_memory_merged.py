"""Tests for FamilyMemoryView, the read-only merged view across persona shards."""

from __future__ import annotations

import itertools
from pathlib import Path

import pytest

from sakthai.config import memory_db_path
from sakthai.memory.merged import FamilyMemoryView, ShardedFact
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent persona_memory_db_path() — which reads Path.home() directly,
    independent of SAKTHAI_HOME, by design — from resolving to the real
    machine's home directory for any persona a test's shard_paths doesn't
    explicitly cover."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "unused-home")


@pytest.fixture
def shard_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "sakthai": tmp_path / "sakthai.db",
        "sakking": tmp_path / "sakking.db",
        "saksee": tmp_path / "saksee.db",
        # Point the legacy/unscoped fallback at a nonexistent path so tests
        # never accidentally pick up the real ~/.sakthai/memory.db.
        "shared": tmp_path / "no-such-legacy-db.db",
    }


def _seed(
    path: Path, facts: list[tuple[str, str, str | None]], obs: list[tuple[str, float]]
) -> None:
    """Seed a shard with (value, kind, key) facts and (summary, weight) observations."""
    with MemoryStore(path) as store:
        for value, kind, key in facts:
            store.add_fact(value, kind=kind, key=key)
        for summary, weight in obs:
            store.add_observation(summary, weight=weight)


def test_missing_shards_are_skipped_silently(tmp_path: Path) -> None:
    shard_paths = {
        "sakthai": tmp_path / "does-not-exist.db",
        "shared": tmp_path / "no-such-legacy-db.db",
    }
    with FamilyMemoryView(shard_paths=shard_paths) as view:
        assert view.list_facts() == []
        assert view.top_observations() == []


def test_unscoped_store_is_included_by_default(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    shard_paths["shared"] = tmp_path / "legacy.db"
    _seed(shard_paths["shared"], [("unattributed note", "note", None)], [])
    _seed(shard_paths["sakthai"], [("attributed note", "note", "k")], [])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        assert {f.persona for f in view.list_facts()} == {"shared", "sakthai"}


def test_include_unscoped_false_leaves_the_legacy_store_out(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    shard_paths["shared"] = tmp_path / "legacy.db"
    _seed(shard_paths["shared"], [("unattributed note", "note", None)], [])
    _seed(shard_paths["sakthai"], [("attributed note", "note", "k")], [])

    with FamilyMemoryView(["sakthai"], shard_paths=shard_paths, include_unscoped=False) as view:
        assert {f.persona for f in view.list_facts()} == {"sakthai"}


def test_include_unscoped_false_also_excludes_its_observations(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    shard_paths["shared"] = tmp_path / "legacy.db"
    _seed(shard_paths["shared"], [], [("legacy observation", 3.0)])
    _seed(shard_paths["sakthai"], [], [("scoped observation", 1.0)])

    with FamilyMemoryView(["sakthai"], shard_paths=shard_paths, include_unscoped=False) as view:
        assert [o.persona for o in view.top_observations()] == ["sakthai"]


def test_omitting_the_shared_key_is_not_how_you_exclude_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing "shared" key falls back to memory_db_path(), not to nothing.

    This is the trap `include_unscoped` exists to avoid: filtering the key out
    of `shard_paths` sends the view to the real ~/.sakthai/memory.db rather
    than excluding the unscoped store.
    """
    fallback_home = tmp_path / "fallback-home"
    (fallback_home / ".sakthai").mkdir(parents=True)
    # `memory_db_path()` reads SAKTHAI_HOME before falling back to Path.home(),
    # so the conftest `_isolate_home` default would shadow the fallback this
    # test exists to exercise. Opting out is the point, not a workaround.
    monkeypatch.delenv("SAKTHAI_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: fallback_home)
    _seed(fallback_home / ".sakthai" / "memory.db", [("from the fallback", "note", None)], [])

    with FamilyMemoryView(["sakthai"], shard_paths={"sakthai": tmp_path / "none.db"}) as view:
        assert [f.persona for f in view.list_facts()] == ["shared"]

    with FamilyMemoryView(
        ["sakthai"], shard_paths={"sakthai": tmp_path / "none.db"}, include_unscoped=False
    ) as view:
        assert view.list_facts() == []


def test_list_facts_merges_across_shards_tagged_with_persona(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    _seed(shard_paths["sakthai"], [("likes tea", "pref", "drink")], [])
    _seed(shard_paths["sakking"], [("likes code", "pref", "hobby")], [])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        facts = view.list_facts()

    assert len(facts) == 2
    assert all(isinstance(f, ShardedFact) for f in facts)
    by_persona = {f.persona: f.fact.value for f in facts}
    assert by_persona == {"sakthai": "likes tea", "sakking": "likes code"}


def test_list_facts_dedupes_by_kind_and_key_keeping_newest(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    # Same (kind, key) written to two shards — only the more-recently-updated
    # copy should survive the merge, not both.
    with MemoryStore(shard_paths["sakthai"]) as store:
        store.add_fact("stale value", kind="pref", key="theme")
    with MemoryStore(shard_paths["sakking"]) as store:
        store.add_fact("fresh value", kind="pref", key="theme")

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        facts = view.list_facts()

    matching = [f for f in facts if f.fact.key == "theme"]
    assert len(matching) == 1
    assert matching[0].fact.value == "fresh value"
    assert matching[0].persona == "sakking"


def test_top_observations_dedupes_by_summary_keeping_highest_weight(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    with MemoryStore(shard_paths["sakthai"]) as store:
        store.add_observation("Beer prefers concise replies", weight=0.4)
    with MemoryStore(shard_paths["saksee"]) as store:
        store.add_observation("Beer prefers concise replies", weight=0.9)

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        obs = view.top_observations()

    assert len(obs) == 1
    assert obs[0].observation.weight == 0.9
    assert obs[0].persona == "saksee"


def test_search_merges_facts_and_observations_across_shards(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    _seed(shard_paths["sakthai"], [("deploys on Fridays", "note", None)], [])
    _seed(shard_paths["sakking"], [], [("Team avoids Friday deploys", 0.7)])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        facts, obs = view.search("friday")

    assert any("deploys on Fridays" in f.fact.value for f in facts)
    assert any("Friday deploys" in o.observation.summary for o in obs)


def test_limit_is_respected_after_merge(tmp_path: Path, shard_paths: dict[str, Path]) -> None:
    with MemoryStore(shard_paths["sakthai"]) as store:
        for i in range(5):
            store.add_fact(f"fact {i}", kind="note")

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        facts = view.list_facts(limit=2)

    assert len(facts) == 2


def test_personas_filter_narrows_which_shards_open(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    _seed(shard_paths["sakthai"], [("only in sakthai", "note", None)], [])
    _seed(shard_paths["sakking"], [("only in sakking", "note", None)], [])

    with FamilyMemoryView(personas=["sakthai"], shard_paths=shard_paths) as view:
        facts = view.list_facts()

    assert len(facts) == 1
    assert facts[0].fact.value == "only in sakthai"


@pytest.fixture
def ticking_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """One second per write, so "newest" never rests on a same-second tie."""
    ticks = itertools.count(1_700_000_000)
    monkeypatch.setattr("sakthai.memory.store._now", lambda: next(ticks))


@pytest.mark.usefixtures("ticking_clock")
def test_find_facts_reads_a_tagged_note_from_a_siblings_shard(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    """The SOUL hand-off case: SakKing reads the summary SakThai wrote to its own shard."""
    with MemoryStore(shard_paths["sakthai"]) as store:
        store.add_fact("HOUSEHOLD CHARGE SUMMARY | old", tags=["charge-summary"])
        store.add_fact("HOUSEHOLD CHARGE SUMMARY | new", tags=["charge-summary"])
        store.add_fact("HOUSEHOLD CHARGE SUMMARY | untagged")
    with MemoryStore(shard_paths["sakking"]) as store:
        store.add_fact("CHARGE: sakking | 80%", tags=["charge-report"])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        newest = view.find_facts("HOUSEHOLD CHARGE SUMMARY", ["charge-summary"], limit=1)
        by_tag = view.find_facts(tags=["charge-summary"])

    assert [(f.persona, f.fact.value) for f in newest] == [
        ("sakthai", "HOUSEHOLD CHARGE SUMMARY | new")
    ]
    assert {f.fact.value for f in by_tag} == {
        "HOUSEHOLD CHARGE SUMMARY | old",
        "HOUSEHOLD CHARGE SUMMARY | new",
    }


def test_a_vm_persona_reads_a_note_its_sibling_wrote(monkeypatch: pytest.MonkeyPatch) -> None:
    """The VM layout: each persona runs with SAKTHAI_HOME=$HOME/.sakthai/<self>.

    SakSee writes a ban to its own store; SakTan, running as itself, must find it.
    Shards used to resolve under SAKTHAI_HOME, which put SakSee's shard at
    ~/.sakthai/saktan/saksee/memory.db for SakTan, so the read came back empty.
    """
    family_root = Path.home() / ".sakthai"
    monkeypatch.setenv("SAKTHAI_HOME", str(family_root / "saksee"))
    with MemoryStore(memory_db_path()) as store:
        store.add_fact("RATE LIMIT BAN: example.com", tags=["rate-limit-ban"])

    monkeypatch.setenv("SAKTHAI_HOME", str(family_root / "saktan"))
    with FamilyMemoryView() as view:
        found = view.find_facts(tags=["rate-limit-ban"])

    assert [(f.persona, f.fact.value) for f in found] == [("saksee", "RATE LIMIT BAN: example.com")]


def test_find_facts_requires_every_tag_even_past_the_limit(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    """Later tags are applied after SQL's LIMIT would have cut the candidates short."""
    with MemoryStore(shard_paths["sakking"]) as store:
        store.add_fact(
            "CYCLE INTERRUPTED: sakking | resumable", tags=["cycle-interrupted", "resumable"]
        )
        for i in range(3):
            store.add_fact(f"CYCLE INTERRUPTED: sakking | done {i}", tags=["cycle-interrupted"])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        found = view.find_facts(tags=["cycle-interrupted", "resumable"], limit=1)
        by_query = view.find_facts("CYCLE INTERRUPTED", ["resumable"], limit=1)

    assert [f.fact.value for f in found] == ["CYCLE INTERRUPTED: sakking | resumable"]
    assert [f.fact.value for f in by_query] == ["CYCLE INTERRUPTED: sakking | resumable"]


def test_find_facts_needs_a_filter(tmp_path: Path, shard_paths: dict[str, Path]) -> None:
    with FamilyMemoryView(shard_paths=shard_paths) as view, pytest.raises(ValueError):
        view.find_facts(tags=["  "])


def test_rejects_unknown_persona_name(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown persona"):
        FamilyMemoryView(personas=["not-a-real-persona"])


def test_render_prompt_block_groups_by_persona(
    tmp_path: Path, shard_paths: dict[str, Path]
) -> None:
    _seed(shard_paths["sakthai"], [("likes tea", "pref", "drink")], [])
    _seed(shard_paths["sakking"], [], [("ships fast", 0.8)])

    with FamilyMemoryView(shard_paths=shard_paths) as view:
        block = view.render_prompt_block()

    assert "sakthai" in block
    assert "sakking" in block
    assert "likes tea" in block
    assert "ships fast" in block
    assert "BEGIN UNTRUSTED DATA" in block
    assert "END UNTRUSTED DATA" in block


def test_render_prompt_block_empty_when_no_shards_have_data(tmp_path: Path) -> None:
    shard_paths = {
        "sakthai": tmp_path / "empty.db",
        "shared": tmp_path / "no-such-legacy-db.db",
    }
    _seed(shard_paths["sakthai"], [], [])
    with FamilyMemoryView(shard_paths=shard_paths) as view:
        assert view.render_prompt_block() == ""
