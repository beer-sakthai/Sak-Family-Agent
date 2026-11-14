"""The six stages of the Dream → Growth working cycle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Stage(StrEnum):
    DREAM = "dream"
    HOPE = "hope"
    CARE = "care"
    JOY = "joy"
    TRUST = "trust"
    GROWTH = "growth"


@dataclass(frozen=True)
class StageInfo:
    stage: Stage
    number: int
    goal: str
    commands: tuple[str, ...]
    guidance: str


STAGES: tuple[StageInfo, ...] = (
    StageInfo(
        stage=Stage.DREAM,
        number=1,
        goal="Define the vision or task",
        commands=("memory show",),
        guidance="Explore options and recall past context; don't implement yet.",
    ),
    StageInfo(
        stage=Stage.HOPE,
        number=2,
        goal="Engineer a solution",
        commands=("learn",),
        guidance="Propose concrete approaches and capture key decisions with `sakthai learn`.",
    ),
    StageInfo(
        stage=Stage.CARE,
        number=3,
        goal="Refine quality — concurrency and performance",
        commands=("learn",),
        guidance="Audit correctness, race conditions, and performance; record findings.",
    ),
    StageInfo(
        stage=Stage.JOY,
        number=4,
        goal="Package and ship",
        commands=("memory stats",),
        guidance="Focus on packaging and CI; celebrate what shipped.",
    ),
    StageInfo(
        stage=Stage.TRUST,
        number=5,
        goal="Secure the foundation",
        commands=("doctor",),
        guidance="Run `sakthai doctor`, check boundaries, and verify idempotency.",
    ),
    StageInfo(
        stage=Stage.GROWTH,
        number=6,
        goal="Learn and grow",
        commands=("memory consolidate",),
        guidance="Capture learnings into memory, then loop back to Dream.",
    ),
)

_ORDER: tuple[Stage, ...] = tuple(s.stage for s in STAGES)
_BY_STAGE: dict[Stage, StageInfo] = {s.stage: s for s in STAGES}


def stage_info(stage: Stage) -> StageInfo:
    return _BY_STAGE[stage]


def next_stage(stage: Stage) -> Stage:
    index = _ORDER.index(stage)
    return _ORDER[(index + 1) % len(_ORDER)]
