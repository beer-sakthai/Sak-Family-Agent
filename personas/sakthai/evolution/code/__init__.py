"""Phase 4: Code Evolution via Darwinian Evolver.

Provides GitBasedOrganism, CompositeFitnessEvaluator, and DarwinianCodeEvolver
for test-gated, AST-validated code evolution on agent tools.
"""

from .evolve_code import DarwinianCodeEvolver, EvolutionResult, GenerationRecord, evolve_tool_code
from .fitness import CodeFitnessScore, CompositeFitnessEvaluator
from .organism import GitBasedOrganism, OrganismMutationRecord

__all__ = [
    "GitBasedOrganism",
    "OrganismMutationRecord",
    "CodeFitnessScore",
    "CompositeFitnessEvaluator",
    "DarwinianCodeEvolver",
    "EvolutionResult",
    "GenerationRecord",
    "evolve_tool_code",
]
