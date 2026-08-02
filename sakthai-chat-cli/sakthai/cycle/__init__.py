"""The 6-stage Dream → Growth cycle and its persisted state."""

from __future__ import annotations

from .stages import STAGES, Stage, StageInfo, next_stage, stage_info
from .state import advance_stage, get_current_stage, set_stage

__all__ = [
    "STAGES",
    "Stage",
    "StageInfo",
    "advance_stage",
    "get_current_stage",
    "next_stage",
    "set_stage",
    "stage_info",
]
