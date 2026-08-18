"""Persona Evolution Optimizer and Evaluation Harness."""

from __future__ import annotations

import difflib
import uuid

from sakthai.evolution.feedback import FeedbackCollector
from sakthai.evolution.models import (
    EvolutionVariant,
    MutationScore,
)
from sakthai.evolution.registry import EvolutionRegistry


class PersonaEvolver:
    """Automates prompt mutations, benchmark evaluations, and promotion decisions."""

    def __init__(
        self,
        registry: EvolutionRegistry,
        feedback: FeedbackCollector | None = None,
    ) -> None:
        self.registry = registry
        self.feedback = feedback or FeedbackCollector(db_path=registry.db_path)

    def generate_mutation(
        self,
        persona: str,
        focus_area: str = "tool_discipline",
        mutation_directive: str | None = None,
    ) -> EvolutionVariant:
        """Generate a structured candidate prompt mutation based on focus area."""
        active = self.registry.get_active_checkpoint(persona)
        if not active:
            active = self.registry.initialize_persona(
                persona,
                f"You are {persona.title()}, a specialized autonomous Sak Family agent.",
            )

        current_prompt = active.active_prompt
        next_gen = active.generation + 1

        # Synthesize prompt mutation based on focus area
        mutated_lines = current_prompt.splitlines()
        rationale = ""

        if focus_area == "tool_discipline":
            rule = "Strict Tool Discipline: Always validate input arguments schema before executing tool calls. Avoid redundant calls."
            if rule not in current_prompt:
                mutated_lines.append(f"\n## Operating Protocol\n{rule}")
            rationale = "Injected strict tool argument verification rules to suppress invalid tool invocation patterns."
        elif focus_area == "conciseness":
            rule = "Communication Style: Deliver direct, actionable responses. Avoid boilerplate greetings or repeated context summaries."
            if rule not in current_prompt:
                mutated_lines.append(f"\n## Communication Style\n{rule}")
            rationale = "Enforced high-density communication rules to improve token efficiency."
        elif focus_area == "error_recovery":
            rule = "Resilience Protocol: On transient tool or API error, invoke exponential backoff retry up to 3 times before failing gracefully."
            if rule not in current_prompt:
                mutated_lines.append(f"\n## Fault Tolerance\n{rule}")
            rationale = "Added autonomous retry and graceful degradation protocol."
        else:
            custom_directive = mutation_directive or "Enhanced clarity and role precision."
            mutated_lines.append(f"\n## Directives\n{custom_directive}")
            rationale = f"Applied custom mutation directive: {custom_directive}"

        mutated_prompt = "\n".join(mutated_lines)

        diff = "\n".join(
            difflib.unified_diff(
                current_prompt.splitlines(keepends=True),
                mutated_prompt.splitlines(keepends=True),
                fromfile=f"generation_{active.generation}",
                tofile=f"generation_{next_gen}",
            )
        )

        variant = EvolutionVariant(
            variant_id=f"var_{persona.lower()}_g{next_gen}_{uuid.uuid4().hex[:6]}",
            persona=persona.lower(),
            generation=next_gen,
            parent_checkpoint_id=active.checkpoint_id,
            prompt_diff=diff if diff else "No textual diff",
            mutated_prompt=mutated_prompt,
            mutation_rationale=rationale,
            status="draft",
        )

        return variant

    def evaluate_variant(self, variant: EvolutionVariant) -> MutationScore:
        """Run simulated evaluation suite against prompt quality metrics."""
        # Check safety invariant: must contain persona name and no dangerous injection keywords
        has_persona_identity = variant.persona.lower() in variant.mutated_prompt.lower()
        has_forbidden_terms = any(
            t in variant.mutated_prompt.lower() for t in ["ignore all previous", "rm -rf /"]
        )
        passed_safety = has_persona_identity and not has_forbidden_terms

        # Scores
        accuracy = 0.94 if passed_safety else 0.40
        tool_discipline = 0.96 if "tool discipline" in variant.mutated_prompt.lower() else 0.88
        conciseness = 0.92 if "communication style" in variant.mutated_prompt.lower() else 0.85

        composite = (accuracy * 0.4) + (tool_discipline * 0.35) + (conciseness * 0.25)

        score = MutationScore(
            accuracy_score=accuracy,
            tool_discipline_score=tool_discipline,
            conciseness_score=conciseness,
            composite_score=composite,
            passed_safety_gate=passed_safety,
        )

        variant.score = score
        variant.status = "evaluated"
        self.registry.save_variant(variant)
        return score

    def auto_evolve_step(
        self, persona: str, focus_area: str = "tool_discipline"
    ) -> tuple[EvolutionVariant, bool]:
        """Execute a full self-evolution cycle step: Mutate -> Evaluate -> Promote if superior."""
        variant = self.generate_mutation(persona, focus_area=focus_area)
        score = self.evaluate_variant(variant)

        active = self.registry.get_active_checkpoint(persona)
        baseline_score = active.composite_score if active else 0.80

        should_promote = score.passed_safety_gate and score.composite_score > baseline_score

        if should_promote:
            self.registry.promote_variant(variant.variant_id)
            variant.status = "promoted"
        else:
            variant.status = "rejected"

        return variant, should_promote
