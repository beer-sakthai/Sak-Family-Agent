"""Defines the stages of the SakThai agent's value-driven cycle.

This module contains only pure functions and data structures, making the core
state transition logic easy to test and reason about independently of its
persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Stage(str, Enum):
    """The 6 core value stages of the agent's operational cycle."""

    DREAM = "dream"
    HOPE = "hope"
    CARE = "care"
    JOY = "joy"
    TRUST = "trust"
    GROWTH = "growth"


@dataclass(frozen=True)
class StageInfo:
    """Metadata associated with a stage."""

    stage: Stage
    number: int
    description: str


STAGES = [
    StageInfo(Stage.DREAM, 1, "Define the ideal future and set ambitious goals."),
    StageInfo(Stage.HOPE, 2, "Identify pathways to the dream and build optimism."),
    StageInfo(Stage.CARE, 3, "Act with empathy, ensuring safety and well-being."),
    StageInfo(Stage.JOY, 4, "Find and create moments of happiness and satisfaction."),
    StageInfo(Stage.TRUST, 5, "Build reliability and confidence through consistent action."),
    StageInfo(Stage.GROWTH, 6, "Learn from experience and expand capabilities."),
]

_STAGE_MAP = {s.stage: s for s in STAGES}
_STAGE_ORDER = [s.stage for s in STAGES]


def next_stage(current: Stage) -> Stage:
    """Calculates the next stage in the cycle."""
    current_index = _STAGE_ORDER.index(current)
    next_index = (current_index + 1) % len(_STAGE_ORDER)
    return _STAGE_ORDER[next_index]


def stage_info(stage: Stage) -> StageInfo:
    """Returns the metadata for a given stage."""
    return _STAGE_MAP[stage]