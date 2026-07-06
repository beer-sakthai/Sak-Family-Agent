"""Persist the current cycle stage as a single fact in the memory store."""

from __future__ import annotations

import logging

from ..memory.store import MemoryStore
from .stages import Stage, next_stage

logger = logging.getLogger(__name__)

_CYCLE_KIND = "cycle"
_CYCLE_KEY = "current_stage"


def get_current_stage(store: MemoryStore) -> Stage:
    """Return the stored stage, defaulting to DREAM if unset or invalid."""
    fact = store.get_fact_by_key(_CYCLE_KIND, _CYCLE_KEY)
    if fact is not None:
        try:
            return Stage(fact.value)
        except ValueError:
            logger.warning("Invalid stage value in memory: %s. Falling back to DREAM.", fact.value)
    return Stage.DREAM


def set_stage(store: MemoryStore, stage: Stage) -> None:
    """Overwrite the stored stage."""
    store.delete_facts_by_key(_CYCLE_KIND, _CYCLE_KEY)
    store.add_fact(stage.value, kind=_CYCLE_KIND, key=_CYCLE_KEY)


def advance_stage(store: MemoryStore) -> Stage:
    """Move to and persist the next stage, returning it."""
    upcoming = next_stage(get_current_stage(store))
    set_stage(store, upcoming)
    return upcoming
