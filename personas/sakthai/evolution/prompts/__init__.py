"""Phase 3: System Prompt Evolution.

Provides section-as-DSPy-parameter wrappers and behavioral evaluators
for the 5 evolvable system prompt sections.
"""

from .evolve_prompts import (
    PromptEvalExample,
    build_synthetic_prompt_dataset,
    evaluate_prompt_behavior,
    evolve_prompts,
    prompt_fitness_metric,
    validate_prompt_constraints,
)
from .prompt_module import (
    EvolvablePromptSections,
    PromptEvolutionModule,
    format_prompt_sections,
    parse_evolved_sections,
)

__all__ = [
    "EvolvablePromptSections",
    "PromptEvolutionModule",
    "format_prompt_sections",
    "parse_evolved_sections",
    "PromptEvalExample",
    "build_synthetic_prompt_dataset",
    "evaluate_prompt_behavior",
    "evolve_prompts",
    "prompt_fitness_metric",
    "validate_prompt_constraints",
]
