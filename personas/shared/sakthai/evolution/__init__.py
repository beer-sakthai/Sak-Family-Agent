"""Autonomous Multi-Agent Self-Evolution Subsystem.

Provides trajectory feedback collection, automated prompt mutation optimization,
behavioral evaluation benchmarks, and safe checkpoint rollbacks.
"""

from sakthai.evolution.evolver import PersonaEvolver
from sakthai.evolution.feedback import FeedbackCollector
from sakthai.evolution.models import (
    EvolutionCheckpoint,
    EvolutionVariant,
    MutationScore,
    TrajectoryFeedback,
)
from sakthai.evolution.registry import EvolutionRegistry

__all__ = [
    "EvolutionCheckpoint",
    "EvolutionRegistry",
    "EvolutionVariant",
    "FeedbackCollector",
    "MutationScore",
    "PersonaEvolver",
    "TrajectoryFeedback",
]
