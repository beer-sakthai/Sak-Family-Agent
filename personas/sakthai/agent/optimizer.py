"""Runtime Evaluator-Optimizer Engine adapting Anthropic Cookbook patterns.

Implements a bounded iterative Evaluator-Optimizer loop where a generator produces
candidate solutions with explicit reasoning, and an evaluator assesses the solution
against specific criteria to provide structured, actionable feedback until the solution
passes or the iteration budget is exhausted.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MAX_OPTIMIZER_ITERATIONS = 3


def _extract_xml_tag(text: str | None, tag: str) -> str:
    """Extract content enclosed in XML-style tags, e.g. <tag>...</tag>."""
    if not text:
        return ""
    pattern = rf"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


@dataclass
class OptimizationIteration:
    """Single iteration record in an Evaluator-Optimizer refinement chain."""

    iteration: int
    thoughts: str
    response: str
    status: str  # "PASS", "NEEDS_IMPROVEMENT", "FAIL"
    feedback: str
    latency_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert iteration to dictionary representation."""
        return asdict(self)


@dataclass
class OptimizationResult:
    """Result of an Evaluator-Optimizer execution."""

    final_response: str
    status: str  # "PASS", "MAX_ITERATIONS", "FAIL"
    iterations: int
    history: list[OptimizationIteration] = field(default_factory=list)
    total_duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return asdict(self)


DEFAULT_GENERATOR_PROMPT = """You are an expert solution generator.
Your goal is to solve the given task thoroughly and accurately.

Think carefully about the problem first.
Provide your reasoning inside <thought>...</thought> tags.
Then, provide your final answer or solution inside <response>...</response> tags.

Task:
{task}
{context_block}
"""

DEFAULT_EVALUATOR_PROMPT = """You are an expert evaluator assessing the quality and correctness of a generated solution.

Evaluate the proposed solution against the task and any provided criteria.

Task:
{task}

{criteria_block}
Proposed Solution:
{content}

Assess whether the proposed solution satisfies all requirements and criteria.
Determine the evaluation status:
- PASS: The solution completely satisfies all requirements and criteria.
- NEEDS_IMPROVEMENT: The solution is on the right track but requires specific corrections or improvements.
- FAIL: The solution is fundamentally flawed, incorrect, or refuses the task.

Output your evaluation strictly using the following XML tags:
<status>PASS, NEEDS_IMPROVEMENT, or FAIL</status>
<feedback>Detailed, actionable feedback explaining why it passed or what specific corrections are needed.</feedback>
"""


class EvaluatorOptimizer:
    """Iterative refinement engine coupling a solution generator and an evaluator."""

    def __init__(
        self,
        evaluator_prompt: str | None = None,
        generator_prompt: str | None = None,
        max_iterations: int = DEFAULT_MAX_OPTIMIZER_ITERATIONS,
        call_fn: Callable[[str], str] | None = None,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.evaluator_prompt = evaluator_prompt
        self.generator_prompt = generator_prompt
        self.max_iterations = max(0, max_iterations)
        self.call_fn = call_fn
        self.model = model
        self.provider = provider

    def _call(self, prompt: str) -> str:
        """Execute a single model invocation using call_fn or default loop dispatch."""
        if self.call_fn is not None:
            return self.call_fn(prompt)
        from .loop import DEFAULT_MODEL, run_agent

        target_model = self.model or DEFAULT_MODEL
        kwargs: dict[str, Any] = {
            "fast": True,
            "stateless": True,
            "tools": (),
            "model": target_model,
        }
        if self.provider:
            kwargs["provider"] = self.provider
        result = run_agent(prompt, **kwargs)
        return result.text

    def generate(self, task: str, context: str = "") -> tuple[str, str]:
        """Generate a candidate solution and reasoning thoughts for the given task.

        Returns:
            tuple[str, str]: (response, thoughts)
        """
        if self.generator_prompt:
            if "{task}" in self.generator_prompt:
                try:
                    prompt = self.generator_prompt.format(
                        task=task,
                        context=context,
                        context_block=f"\nContext and Feedback from previous iteration:\n{context}\n"
                        if context
                        else "",
                    )
                except KeyError:
                    prompt = f"{self.generator_prompt}\n\nTask:\n{task}"
                    if context:
                        prompt += f"\n\nContext and Feedback:\n{context}"
            else:
                prompt = f"{self.generator_prompt}\n\nTask:\n{task}"
                if context:
                    prompt += f"\n\nContext and Feedback:\n{context}"
        else:
            context_block = (
                f"\nContext and Feedback from previous iteration:\n{context}\n" if context else ""
            )
            prompt = DEFAULT_GENERATOR_PROMPT.format(task=task, context_block=context_block)

        raw = self._call(prompt)

        # XML extraction with fallbacks
        thoughts = _extract_xml_tag(raw, "thought")
        if not thoughts:
            thoughts = _extract_xml_tag(raw, "thoughts")

        response = _extract_xml_tag(raw, "response")
        if not response:
            response = _extract_xml_tag(raw, "solution")

        if not response:
            clean = re.sub(
                r"<(thought|thoughts)>.*?</\1>", "", raw, flags=re.DOTALL | re.IGNORECASE
            ).strip()
            response = clean if clean else raw.strip()

        return response, thoughts

    def evaluate(self, task: str, content: str, criteria: str = "") -> tuple[str, str]:
        """Evaluate a candidate solution against task and criteria.

        Returns:
            tuple[str, str]: (status, feedback) where status is PASS, NEEDS_IMPROVEMENT, or FAIL.
        """
        if self.evaluator_prompt:
            if "{task}" in self.evaluator_prompt and "{content}" in self.evaluator_prompt:
                try:
                    prompt = self.evaluator_prompt.format(
                        task=task,
                        content=content,
                        criteria=criteria,
                        criteria_block=f"Evaluation Criteria:\n{criteria}\n\n" if criteria else "",
                    )
                except KeyError:
                    prompt = (
                        f"{self.evaluator_prompt}\n\nTask:\n{task}\n\nProposed Solution:\n{content}"
                    )
                    if criteria:
                        prompt += f"\n\nEvaluation Criteria:\n{criteria}"
            else:
                prompt = (
                    f"{self.evaluator_prompt}\n\nTask:\n{task}\n\nProposed Solution:\n{content}"
                )
                if criteria:
                    prompt += f"\n\nEvaluation Criteria:\n{criteria}"
        else:
            criteria_block = f"Evaluation Criteria:\n{criteria}\n\n" if criteria else ""
            prompt = DEFAULT_EVALUATOR_PROMPT.format(
                task=task,
                criteria_block=criteria_block,
                content=content,
            )

        raw = self._call(prompt)

        raw_status = _extract_xml_tag(raw, "status").strip().upper()
        if raw_status in ("PASS", "NEEDS_IMPROVEMENT", "FAIL"):
            status = raw_status
        elif "FAIL" in raw_status:
            status = "FAIL"
        elif "NEEDS_IMPROVEMENT" in raw_status or "IMPROV" in raw_status:
            status = "NEEDS_IMPROVEMENT"
        elif "PASS" in raw_status:
            status = "PASS"
        else:
            # Fallback if <status> tag missing or malformed
            text_upper = raw.upper()
            if "STATUS: PASS" in text_upper or "<STATUS>PASS" in text_upper:
                status = "PASS"
            elif "STATUS: FAIL" in text_upper or "<STATUS>FAIL" in text_upper:
                status = "FAIL"
            elif "STATUS: NEEDS_IMPROVEMENT" in text_upper or "NEEDS IMPROVEMENT" in text_upper:
                status = "NEEDS_IMPROVEMENT"
            elif "PASS" in text_upper and "FAIL" not in text_upper and "IMPROV" not in text_upper:
                status = "PASS"
            elif "FAIL" in text_upper:
                status = "FAIL"
            else:
                status = "NEEDS_IMPROVEMENT"

        feedback = _extract_xml_tag(raw, "feedback")
        if not feedback:
            clean = re.sub(
                r"<status>.*?</status>", "", raw, flags=re.DOTALL | re.IGNORECASE
            ).strip()
            feedback = clean if clean else raw.strip()

        return status, feedback

    def optimize(
        self,
        task: str,
        criteria: str = "",
        initial_context: str = "",
    ) -> OptimizationResult:
        """Execute the bounded feedback loop until PASS, FAIL, or max_iterations reached."""
        history: list[OptimizationIteration] = []
        context = initial_context
        total_start = time.perf_counter()
        final_response = ""
        final_status = "MAX_ITERATIONS"

        if self.max_iterations <= 0:
            return OptimizationResult(
                final_response="",
                status="MAX_ITERATIONS",
                iterations=0,
                history=[],
                total_duration_s=0.0,
            )

        for i in range(1, self.max_iterations + 1):
            iter_start = time.perf_counter()
            response, thoughts = self.generate(task, context=context)
            final_response = response
            status, feedback = self.evaluate(task, response, criteria=criteria)
            latency = time.perf_counter() - iter_start

            iteration_record = OptimizationIteration(
                iteration=i,
                thoughts=thoughts,
                response=response,
                status=status,
                feedback=feedback,
                latency_s=latency,
            )
            history.append(iteration_record)

            if status == "PASS":
                final_status = "PASS"
                break
            elif status == "FAIL":
                final_status = "FAIL"
                break
            elif status == "NEEDS_IMPROVEMENT":
                if i >= self.max_iterations:
                    final_status = "MAX_ITERATIONS"
                    break
                context = (
                    f"Previous attempt (iteration {i}):\n{response}\n\n"
                    f"Evaluator feedback:\n{feedback}"
                )
            else:
                if i >= self.max_iterations:
                    final_status = "MAX_ITERATIONS"
                    break
                context = (
                    f"Previous attempt (iteration {i}):\n{response}\n\n"
                    f"Evaluator feedback:\n{feedback}"
                )

        total_duration = time.perf_counter() - total_start
        return OptimizationResult(
            final_response=final_response,
            status=final_status,
            iterations=len(history),
            history=history,
            total_duration_s=total_duration,
        )


def optimize_solution(
    task: str,
    criteria: str = "",
    max_iterations: int = DEFAULT_MAX_OPTIMIZER_ITERATIONS,
    call_fn: Callable[[str], str] | None = None,
    *,
    evaluator_prompt: str | None = None,
    generator_prompt: str | None = None,
    model: str | None = None,
    provider: str | None = None,
    initial_context: str = "",
) -> OptimizationResult:
    """Run an Evaluator-Optimizer loop on a task until it passes or hits max_iterations."""
    optimizer = EvaluatorOptimizer(
        evaluator_prompt=evaluator_prompt,
        generator_prompt=generator_prompt,
        max_iterations=max_iterations,
        call_fn=call_fn,
        model=model,
        provider=provider,
    )
    return optimizer.optimize(task=task, criteria=criteria, initial_context=initial_context)


__all__ = [
    "DEFAULT_MAX_OPTIMIZER_ITERATIONS",
    "EvaluatorOptimizer",
    "OptimizationIteration",
    "OptimizationResult",
    "_extract_xml_tag",
    "optimize_solution",
]
