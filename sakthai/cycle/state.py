"""Manages the persistence and advancement of the agent's cycle state.

This module acts as the bridge between the abstract state definitions in
`stages.py` and the concrete persistence layer in `memory/store.py`.
"""

from __future__ import annotations

import logging

from sakthai.cycle.stages import Stage, next_stage
from sakthai.memory.store import MemoryStore

_CYCLE_KIND = "cycle"
_CYCLE_KEY = "current_stage"

log = logging.getLogger(__name__)


def get_current_stage(store: MemoryStore) -> Stage:
    """Retrieves the current stage from the memory store.

    If the stage is not set or is invalid, it defaults to DREAM and logs a
    warning.

    Args:
        store: The memory store to query.

    Returns:
        The current operational stage.
    """
    fact = store.get_fact(kind=_CYCLE_KIND, key=_CYCLE_KEY)
    if not fact or not fact.value:
        return Stage.DREAM

    try:
        return Stage(fact.value)
    except ValueError:
        log.warning(
            "Invalid stage value '%s' found in memory. Defaulting to %s.",
            fact.value,
            Stage.DREAM.value,
        )
        return Stage.DREAM


def set_stage(store: MemoryStore, stage: Stage) -> None:
    """Persists the given stage to the memory store.

    Args:
        store: The memory store to update.
        stage: The stage to set as the current one.
    """
    store.add_fact(stage.value, kind=_CYCLE_KIND, key=_CYCLE_KEY)


def advance_stage(store: MemoryStore) -> Stage:
    """Advances the agent to the next stage in the cycle and persists it.

    Returns:
        The new stage after advancing.
    """
    current = get_current_stage(store)
    new_stage = next_stage(current)
    set_stage(store, new_stage)
    log.info("Advanced cycle stage from %s to %s.", current.value, new_stage.value)
    return new_stage