"""DSPy module and section-as-parameter wrapper for System Prompt Evolution.

Exposes PromptEvolutionModule and EvolvablePromptSections representing the 5
evolvable sections from sakthai.agent.prompt_builder:
- DEFAULT_AGENT_IDENTITY
- MEMORY_GUIDANCE
- SESSION_SEARCH_GUIDANCE
- SKILLS_GUIDANCE
- PLATFORM_HINTS
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

try:
    import dspy
    _HAS_DSPY = True
except ImportError:
    _HAS_DSPY = False

    class _MockSignature:
        def __init__(self, instructions: str = ""):
            self.__doc__ = instructions

        @classmethod
        def with_instructions(cls, instructions: str) -> Any:
            class _BoundSignature(cls):  # type: ignore[valid-type, misc]
                pass

            _BoundSignature.__doc__ = instructions
            return _BoundSignature

    class _MockPredict:
        def __init__(self, signature: Any):
            self.signature = signature

    class _MockChainOfThought:
        def __init__(self, signature: Any):
            self.signature = signature
            self.predict = _MockPredict(signature)

        def __call__(self, task_input: str) -> Any:
            return _MockPrediction(agent_response=f"Executed task: {task_input}")

    class _MockPrediction:
        def __init__(self, agent_response: str = ""):
            self.agent_response = agent_response

    class _MockModule:
        pass

    class _MockField:
        def __init__(self, desc: str = ""):
            self.desc = desc

    class _MockDSPy:
        Module = _MockModule
        Signature = _MockSignature
        ChainOfThought = _MockChainOfThought
        Prediction = _MockPrediction
        InputField = _MockField
        OutputField = _MockField

    dspy = _MockDSPy()  # type: ignore[assignment]

from sakthai.agent.prompt_builder import (
    DEFAULT_AGENT_IDENTITY,
    MEMORY_GUIDANCE,
    PLATFORM_HINTS,
    SESSION_SEARCH_GUIDANCE,
    SKILLS_GUIDANCE,
    build_system_prompt,
)


@dataclass
class EvolvablePromptSections:
    """Dataclass encapsulating the 5 evolvable system prompt sections."""

    identity: str = DEFAULT_AGENT_IDENTITY
    memory_guidance: str = MEMORY_GUIDANCE
    session_guidance: str = SESSION_SEARCH_GUIDANCE
    skills_guidance: str = SKILLS_GUIDANCE
    platform_hints: str = PLATFORM_HINTS

    def to_dict(self) -> dict[str, str]:
        """Convert prompt sections to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvolvablePromptSections:
        """Create prompt sections from a dictionary with baseline fallbacks."""
        return cls(
            identity=str(data.get("identity") or DEFAULT_AGENT_IDENTITY).strip(),
            memory_guidance=str(data.get("memory_guidance") or MEMORY_GUIDANCE).strip(),
            session_guidance=str(data.get("session_guidance") or SESSION_SEARCH_GUIDANCE).strip(),
            skills_guidance=str(data.get("skills_guidance") or SKILLS_GUIDANCE).strip(),
            platform_hints=str(data.get("platform_hints") or PLATFORM_HINTS).strip(),
        )

    def render_full_prompt(
        self,
        memory_block: str | None = None,
        skills_block: str | None = None,
        prefix: str | None = None,
        fast: bool = False,
    ) -> str:
        """Render the complete system prompt using sakthai.agent.prompt_builder."""
        return build_system_prompt(
            memory_block=memory_block,
            skills_block=skills_block,
            prefix=prefix,
            fast=fast,
            identity=self.identity,
            memory_guidance=self.memory_guidance,
            session_guidance=self.session_guidance,
            skills_guidance=self.skills_guidance,
            platform_hints=self.platform_hints,
        )


def format_prompt_sections(sections: EvolvablePromptSections) -> str:
    """Format prompt sections into marked blocks for DSPy signature instructions."""
    blocks = [
        "You are an AI agent guided by the modular system prompt sections below.",
        "",
        "[SECTION DEFAULT_AGENT_IDENTITY]",
        sections.identity.strip(),
        "",
        "[SECTION MEMORY_GUIDANCE]",
        sections.memory_guidance.strip(),
        "",
        "[SECTION SESSION_SEARCH_GUIDANCE]",
        sections.session_guidance.strip(),
        "",
        "[SECTION SKILLS_GUIDANCE]",
        sections.skills_guidance.strip(),
        "",
        "[SECTION PLATFORM_HINTS]",
        sections.platform_hints.strip(),
        "",
        "Execute the task directly, faithfully adhering to all sections above.",
    ]
    return "\n".join(blocks)


def parse_evolved_sections(text: str) -> EvolvablePromptSections:
    """Parse evolved DSPy signature instructions back into EvolvablePromptSections."""
    pattern = r"\[SECTION\s+([\w_]+)\](.*?)(?=\[SECTION|\Z)"
    matches = list(re.finditer(pattern, text, re.DOTALL))

    parsed: dict[str, str] = {}
    for match in matches:
        sec_name = match.group(1).strip()
        sec_body = match.group(2).strip()
        # Clean trailing instructions footer if present in the last section
        if "Execute the task directly" in sec_body:
            sec_body = sec_body.split("Execute the task directly")[0].strip()
        parsed[sec_name] = sec_body

    return EvolvablePromptSections(
        identity=parsed.get("DEFAULT_AGENT_IDENTITY") or DEFAULT_AGENT_IDENTITY,
        memory_guidance=parsed.get("MEMORY_GUIDANCE") or MEMORY_GUIDANCE,
        session_guidance=parsed.get("SESSION_SEARCH_GUIDANCE") or SESSION_SEARCH_GUIDANCE,
        skills_guidance=parsed.get("SKILLS_GUIDANCE") or SKILLS_GUIDANCE,
        platform_hints=parsed.get("PLATFORM_HINTS") or PLATFORM_HINTS,
    )


class PromptEvolutionModule(dspy.Module):
    """DSPy module that exposes the 5 evolvable prompt sections for GEPA/MIPROv2 optimization."""

    class PredictPromptBehavior(dspy.Signature):
        """Execute the user task following the agent's identity, memory, session, skills, and platform guidance."""

        task_input: str = dspy.InputField(desc="The user query, scenario, or context")
        agent_response: str = dspy.OutputField(
            desc="The agent's direct response or behavioral action"
        )

    def __init__(self, sections: EvolvablePromptSections | None = None):
        super().__init__()
        if sections is None:
            sections = EvolvablePromptSections()
        self.predictor = dspy.ChainOfThought(self.PredictPromptBehavior)
        self.set_sections(sections)

    @property
    def sections(self) -> EvolvablePromptSections:
        """Extract current (potentially mutated) prompt sections from predictor instructions."""
        instructions = getattr(self.predictor.predict.signature, "__doc__", "") or ""
        return parse_evolved_sections(instructions)

    def set_sections(self, sections: EvolvablePromptSections) -> None:
        """Set signature instructions to formatted sections for DSPy optimizers to mutate."""
        formatted = format_prompt_sections(sections)
        self.predictor.predict.signature = self.predictor.predict.signature.with_instructions(
            formatted
        )

    def forward(self, task_input: str) -> dspy.Prediction:
        """Run the forward pass through the predictor."""
        return self.predictor(task_input=task_input)
