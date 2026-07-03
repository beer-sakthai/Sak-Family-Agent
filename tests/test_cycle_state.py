"""Unit tests for the working-cycle state machine.

``sakthai.cycle.stages`` (pure transitions) and ``sakthai.cycle.state`` (store
persistence) were only exercised indirectly through the CLI ``cycle`` commands.
These pin the transition and persistence logic — including the invalid-stage
fallback — directly and in isolation.
"""

from __future__ import annotations

import logging

import pytest

from sakthai.cycle.stages import STAGES, Stage, next_stage, stage_info
from sakthai.cycle.state import advance_stage, get_current_stage, set_stage
from sakthai.memory.store import MemoryStore

_CYCLE_KIND = "cycle"
_CYCLE_KEY = "current_stage"


def test_next_stage_advances_in_order() -> None:
    assert next_stage(Stage.DREAM) == Stage.HOPE
    assert next_stage(Stage.HOPE) == Stage.CARE
    assert next_stage(Stage.CARE) == Stage.JOY
    assert next_stage(Stage.JOY) == Stage.TRUST
    assert next_stage(Stage.TRUST) == Stage.GROWTH


def test_next_stage_wraps_from_growth_to_dream() -> None:
    assert next_stage(Stage.GROWTH) == Stage.DREAM


def test_next_stage_cycles_back_to_start_after_full_loop() -> None:
    stage = Stage.DREAM
    for _ in range(len(STAGES)):
        stage = next_stage(stage)
    assert stage == Stage.DREAM


def test_stage_info_returns_matching_metadata() -> None:
    info = stage_info(Stage.DREAM)
    assert info.stage == Stage.DREAM
    assert info.number == 1
    # Every stage resolves and numbers are 1..N in declaration order.
    assert [stage_info(s.stage).number for s in STAGES] == list(range(1, len(STAGES) + 1))


def test_get_current_stage_defaults_to_dream(store: MemoryStore) -> None:
    assert get_current_stage(store) == Stage.DREAM


def test_set_stage_persists_and_overwrites(store: MemoryStore) -> None:
    set_stage(store, Stage.HOPE)
    assert get_current_stage(store) == Stage.HOPE

    set_stage(store, Stage.TRUST)
    assert get_current_stage(store) == Stage.TRUST
    # Overwrite must not leave a second row behind.
    assert len(store.list_facts()) == 1


def test_advance_stage_returns_and_persists_next(store: MemoryStore) -> None:
    set_stage(store, Stage.DREAM)
    assert advance_stage(store) == Stage.HOPE
    assert get_current_stage(store) == Stage.HOPE


def test_advance_stage_walks_the_full_loop(store: MemoryStore) -> None:
    set_stage(store, Stage.DREAM)
    seen = [advance_stage(store) for _ in range(len(STAGES))]
    assert seen == [
        Stage.HOPE,
        Stage.CARE,
        Stage.JOY,
        Stage.TRUST,
        Stage.GROWTH,
        Stage.DREAM,
    ]


def test_get_current_stage_falls_back_to_dream_on_invalid_value(
    store: MemoryStore, caplog: pytest.LogCaptureFixture
) -> None:
    store.add_fact("not-a-real-stage", kind=_CYCLE_KIND, key=_CYCLE_KEY)

    with caplog.at_level(logging.WARNING, logger="sakthai.cycle.state"):
        assert get_current_stage(store) == Stage.DREAM

    assert any("Invalid stage value" in record.message for record in caplog.records)
