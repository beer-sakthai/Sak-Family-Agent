"""Facts tagged ``no-export`` are local-only: never shown to a model, exported or folded.

The web API bearer token is stored as an ordinary fact tagged ``no-export``. The tag used
to be written but never read, so the token could be ranked into a system prompt, returned by
``recall``/``search``, folded into an observation by ``consolidate_facts``, or carried out by
``export_to_dict`` (memory sync, session checkpoints).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.agent.tools import _family_recall, _family_search, _recall, _search
from sakthai.memory.merged import FamilyMemoryView
from sakthai.memory.session_store import FileSessionStore
from sakthai.memory.store import (
    _NOT_PRIVATE_SQL,
    PRIVATE_FACT_KIND,
    PRIVATE_FACT_TAG,
    MemoryStore,
)

TOKEN = "f3a9c1d27b5e48a0913c6d2e8b7a4f10"


def _add_token(store: MemoryStore) -> int:
    return store.add_fact(
        value=TOKEN, kind="web_auth", key="bearer_token", tags=["system", PRIVATE_FACT_TAG]
    )


def _snapshot_with(facts: list[dict[str, object]]) -> dict[str, object]:
    return {"version": 2, "facts": facts, "observations": []}


def _fact_row(fact_id: int, value: str, tags: list[str] | None = None) -> dict[str, object]:
    return {
        "id": fact_id,
        "kind": "note",
        "key": None,
        "value": value,
        "source_session": None,
        "created_at": 1,
        "updated_at": 1,
        "tags": tags or [],
    }


def test_sql_predicate_names_the_same_tag_as_the_constant() -> None:
    # The SQL spells the tag out (an f-string there trips Bandit B608), so pin the two together.
    assert f"value = '{PRIVATE_FACT_TAG}'" in _NOT_PRIVATE_SQL


def test_readers_hide_private_facts_unless_asked(store: MemoryStore) -> None:
    _add_token(store)
    store.add_fact(value="likes tea", kind="note", tags=["system"])

    assert [f.value for f in store.list_facts()] == ["likes tea"]
    facts, _ = store.search_memory("bearer")
    assert facts == []
    assert [f.value for f in store.search_by_tag("system")] == ["likes tea"]

    assert {f.value for f in store.list_facts(include_private=True)} == {TOKEN, "likes tea"}
    assert [f.value for f in store.search_memory("bearer", include_private=True)[0]] == [TOKEN]
    assert {f.value for f in store.search_by_tag("system", include_private=True)} == {
        TOKEN,
        "likes tea",
    }


def test_lookup_by_key_still_finds_the_token(store: MemoryStore) -> None:
    _add_token(store)
    fact = store.get_fact_by_key("web_auth", "bearer_token")
    assert fact is not None and fact.value == TOKEN


def test_untagged_and_malformed_tag_rows_stay_visible(store: MemoryStore) -> None:
    store.add_fact(value="plain", kind="note")
    store.add_fact(value="tagged", kind="note", tags=["work"])
    fact_id = store.add_fact(value="legacy", kind="note")
    store._conn.execute("UPDATE facts SET tags = 'not json' WHERE id = ?", (fact_id,))
    store._conn.commit()

    assert {f.value for f in store.list_facts()} == {"plain", "tagged", "legacy"}


@pytest.mark.parametrize("query", [None, "show the bearer token", "web_auth bearer_token"])
def test_prompt_block_never_contains_the_token(store: MemoryStore, query: str | None) -> None:
    _add_token(store)
    for i in range(40):  # more than DEFAULT_FACT_LIMIT newer facts
        store.add_fact(value=f"unrelated fact {i}", kind="note")

    block = store.render_prompt_block(query=query)
    assert TOKEN not in block
    assert "web_auth" not in block


def test_prompt_block_does_not_shrink_when_a_private_fact_is_newest(store: MemoryStore) -> None:
    for i in range(30):
        store.add_fact(value=f"older fact {i}", kind="note")
    _add_token(store)  # newest of all

    block = store.render_prompt_block(fact_limit=25)
    assert block.count("- [note]") == 25


def test_consolidate_keeps_private_facts_and_does_not_fold_them(store: MemoryStore) -> None:
    token_id = _add_token(store)
    other_id = store.add_fact(value="old note", kind="note")
    store._conn.execute("UPDATE facts SET updated_at = 1")
    store._conn.commit()

    assert store.consolidate_facts(age_seconds=60) == 1

    assert store.get_fact(token_id) is not None
    assert store.get_fact(other_id) is None
    assert all(TOKEN not in o.summary for o in store.top_observations())


def test_export_omits_private_facts_unless_asked(store: MemoryStore) -> None:
    _add_token(store)
    store.add_fact(value="likes tea", kind="note")

    assert [f["value"] for f in store.export_to_dict()["facts"]] == ["likes tea"]
    exported = store.export_to_dict(include_private=True)
    assert {f["value"] for f in exported["facts"]} == {TOKEN, "likes tea"}


@pytest.mark.parametrize("mode", ["merge", "replace"])
def test_import_never_brings_in_a_private_fact(store: MemoryStore, mode: str) -> None:
    snapshot = _snapshot_with(
        [
            _fact_row(1, "visible"),
            _fact_row(2, "attacker-chosen-token", tags=["system", PRIVATE_FACT_TAG]),
        ]
    )

    imported_facts, _ = store.import_from_dict(snapshot, mode=mode)

    assert imported_facts == 1
    assert {f.value for f in store.list_facts(include_private=True)} == {"visible"}


def test_replace_import_keeps_the_local_token_even_when_ids_collide(store: MemoryStore) -> None:
    token_id = _add_token(store)
    # The snapshot reuses the token row's id for an ordinary fact: replace must not
    # fail on the primary key, and the token must survive the wipe.
    snapshot = _snapshot_with([_fact_row(token_id, "restored note")])

    store.import_from_dict(snapshot, mode="replace")

    token = store.get_fact_by_key("web_auth", "bearer_token")
    assert token is not None and token.value == TOKEN
    assert PRIVATE_FACT_TAG in token.tags
    assert {f.value for f in store.list_facts()} == {"restored note"}


def test_checkpoint_revert_keeps_the_bearer_token(store: MemoryStore, tmp_path: Path) -> None:
    sessions = FileSessionStore(checkpoints_dir=str(tmp_path / "checkpoints"))
    _add_token(store)
    store.add_fact(value="before", kind="note")
    sessions.create_checkpoint("snap", memory_store=store)
    store.add_fact(value="after", kind="note")

    assert TOKEN not in (tmp_path / "checkpoints" / "snap.json").read_text(encoding="utf-8")
    assert sessions.revert_checkpoint("snap", memory_store=store)

    assert {f.value for f in store.list_facts()} == {"before"}
    token = store.get_fact_by_key("web_auth", "bearer_token")
    assert token is not None and token.value == TOKEN


def test_family_view_and_tools_never_return_the_token(store: MemoryStore, tmp_path: Path) -> None:
    _add_token(store)
    store.add_fact(value="likes tea", kind="note")
    shard = tmp_path / "memory.db"

    with FamilyMemoryView(personas=["sakthai"], shard_paths={"sakthai": shard}) as view:
        assert TOKEN not in view.render_prompt_block()
        assert all(sf.fact.value != TOKEN for sf in view.list_facts())
        assert view.search("bearer")[0] == []
        assert view.find_facts("bearer") == []
        assert view.find_facts(tags=[PRIVATE_FACT_TAG]) == []

    assert TOKEN not in _recall({"limit": 50}, store)
    assert TOKEN not in _search({"query": "bearer"}, store)


def test_family_tools_never_return_the_token(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _add_token(store)
    shard = tmp_path / "memory.db"
    monkeypatch.setattr(
        "sakthai.memory.merged.persona_memory_db_path",
        lambda persona: shard if persona == "sakthai" else tmp_path / f"{persona}.db",
    )

    assert TOKEN not in _family_recall({"personas": ["sakthai"], "limit": 50}, store)
    assert TOKEN not in _family_search({"personas": ["sakthai"], "query": "bearer"}, store)


def test_sql_predicate_names_the_same_kind_as_the_constant() -> None:
    assert f"kind <> '{PRIVATE_FACT_KIND}'" in _NOT_PRIVATE_SQL


def test_the_credential_kind_is_private_even_without_the_tag(store: MemoryStore) -> None:
    store.add_fact(value="stray-token", kind=PRIVATE_FACT_KIND, key="bearer_token")
    store.add_fact(value="likes tea", kind="note")

    assert [f.value for f in store.list_facts()] == ["likes tea"]
    assert [f["value"] for f in store.export_to_dict()["facts"]] == ["likes tea"]
    assert store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token") is not None


@pytest.mark.parametrize("mode", ["merge", "replace"])
@pytest.mark.parametrize("tags", [[], ["no-export "], [" no-export"], ["system", "no-export"]])
def test_import_cannot_plant_a_credential(store: MemoryStore, mode: str, tags: list[str]) -> None:
    _add_token(store)
    forged = _fact_row(9, "attacker-chosen-token", tags=tags)
    forged.update(kind=PRIVATE_FACT_KIND, key="bearer_token")

    imported_facts, _ = store.import_from_dict(_snapshot_with([forged]), mode=mode)

    assert imported_facts == 0
    token = store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token")
    assert token is not None and token.value == TOKEN
    assert "attacker-chosen-token" not in {f.value for f in store.list_facts(include_private=True)}


def test_replace_import_keeps_the_private_facts_own_id_when_it_is_free(
    store: MemoryStore,
) -> None:
    token_id = _add_token(store)  # id 1
    store.add_fact(value="kept note", kind="note")  # id 2
    snapshot = store.export_to_dict()
    discarded_id = store.add_fact(value="newer note", kind="note")  # id 3, not in the snapshot

    store.import_from_dict(snapshot, mode="replace")

    token = store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token")
    assert token is not None and token.id == token_id
    # `memory forget <id>` on the discarded note must not hit the private fact.
    assert store.get_fact(discarded_id) is None
    assert store.forget_fact(discarded_id) is False
    assert store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token") is not None


def test_replace_import_moves_a_colliding_private_fact_above_every_other_id(
    store: MemoryStore,
) -> None:
    token_id = _add_token(store)  # id 1
    for i in range(6):
        store.add_fact(value=f"note {i}", kind="note")  # ids 2..7
    # The snapshot reuses the token's id and tops out below the pre-import maximum (7), so
    # the new id has to clear the old maximum, not just the incoming one.
    snapshot = _snapshot_with([_fact_row(token_id, "restored note"), _fact_row(3, "third note")])

    store.import_from_dict(snapshot, mode="replace")

    token = store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token")
    assert token is not None and token.value == TOKEN
    assert token.id == 8
    assert {f.value for f in store.list_facts()} == {"restored note", "third note"}


def test_a_lookalike_kind_is_an_ordinary_fact_and_survives_a_replace_round_trip(
    store: MemoryStore,
) -> None:
    _add_token(store)
    # Kinds are stored as written; only the exact credential kind is the credential.
    store.add_fact(value="dashboard note", kind=f"{PRIVATE_FACT_KIND} ")
    snapshot = store.export_to_dict()
    assert [f["value"] for f in snapshot["facts"]] == ["dashboard note"]

    store.import_from_dict(snapshot, mode="replace")

    assert {f.value for f in store.list_facts()} == {"dashboard note"}
    token = store.get_fact_by_key(PRIVATE_FACT_KIND, "bearer_token")
    assert token is not None and token.value == TOKEN
