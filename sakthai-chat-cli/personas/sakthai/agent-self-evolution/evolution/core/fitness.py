"""Fitness functions for evaluating evolved artifacts.

Uses LLM-as-judge with rubrics to score agent outputs.
Supports length penalties and multi-dimensional scoring.
"""

from dataclasses import dataclass

import dspy

from evolution.core.config import EvolutionConfig


@dataclass
class FitnessScore:
    """Multi-dimensional fitness score."""

    correctness: float = 0.0  # Did the agent produce correct output? (0-1)
    procedure_following: float = 0.0  # Did it follow the skill's procedure? (0-1)
    conciseness: float = 0.0  # Was it appropriately concise? (0-1)
    length_penalty: float = 0.0  # Penalty for being too verbose (0-1, 0 = no penalty)
    feedback: str = ""  # Textual feedback for GEPA's reflective analysis

    @property
    def composite(self) -> float:
        """Weighted composite score."""
        raw = 0.5 * self.correctness + 0.3 * self.procedure_following + 0.2 * self.conciseness
        return max(0.0, raw - self.length_penalty)


class LLMJudge:
    """LLM-as-judge scorer with rubric-based evaluation.

    Scores agent outputs on multiple dimensions and provides
    textual feedback that GEPA can use for reflective mutation.
    """

    class JudgeSignature(dspy.Signature):
        """Evaluate an agent's response against an expected behavior rubric.

        Score the response on three dimensions (0.0 to 1.0 each):
        1. correctness: Did the response correctly address the task?
        2. procedure_following: Did it follow the expected approach/procedure?
        3. conciseness: Was it appropriately concise without omitting important info?

        Also provide specific, actionable feedback on what could be improved.
        """

        task_input: str = dspy.InputField(desc="The task the agent was given")
        expected_behavior: str = dspy.InputField(
            desc="Rubric describing what a good response looks like"
        )
        agent_output: str = dspy.InputField(desc="The agent's actual response")
        skill_text: str = dspy.InputField(desc="The skill/instructions the agent was following")
        correctness: float = dspy.OutputField(
            desc="Score 0.0-1.0: Did the response correctly address the task?"
        )
        procedure_following: float = dspy.OutputField(
            desc="Score 0.0-1.0: Did it follow the expected procedure?"
        )
        conciseness: float = dspy.OutputField(desc="Score 0.0-1.0: Appropriately concise?")
        feedback: str = dspy.OutputField(
            desc="Specific, actionable feedback on what could be improved"
        )

    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.judge = dspy.ChainOfThought(self.JudgeSignature)

    def score(
        self,
        task_input: str,
        expected_behavior: str,
        agent_output: str,
        skill_text: str,
        artifact_size: int | None = None,
        max_size: int | None = None,
    ) -> FitnessScore:
        """Score an agent output using LLM-as-judge."""

        lm = dspy.LM(self.config.eval_model)

        with dspy.context(lm=lm):
            result = self.judge(
                task_input=task_input,
                expected_behavior=expected_behavior,
                agent_output=agent_output,
                skill_text=skill_text,
            )

        # Parse scores (clamp to 0-1)
        correctness = _parse_score(result.correctness)
        procedure_following = _parse_score(result.procedure_following)
        conciseness = _parse_score(result.conciseness)

        # Length penalty
        length_penalty = 0.0
        if artifact_size is not None and max_size is not None:
            ratio = artifact_size / max_size
            if ratio > 0.9:
                # Penalty ramps from 0 at 90% to 0.3 at 100%+
                length_penalty = min(0.3, (ratio - 0.9) * 3.0)

        return FitnessScore(
            correctness=correctness,
            procedure_following=procedure_following,
            conciseness=conciseness,
            length_penalty=length_penalty,
            feedback=str(result.feedback),
        )


def skill_fitness_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """DSPy-compatible metric function for skill optimization.

    This is what gets passed to dspy.GEPA(metric=...).
    Returns a float 0-1 score.
    """
    # The prediction should have an 'output' field with the agent's response
    agent_output = getattr(prediction, "output", "") or ""
    expected = getattr(example, "expected_behavior", "") or ""
    getattr(example, "task_input", "") or ""

    if not agent_output.strip():
        return 0.0

    # Quick heuristic scoring (for speed during optimization)
    # Full LLM-as-judge scoring is expensive — use it selectively
    score = 0.5  # Base score for non-empty output

    # Check if key phrases from expected behavior appear
    expected_lower = expected.lower()
    output_lower = agent_output.lower()

    # Simple keyword overlap as a fast proxy
    expected_words = set(expected_lower.split())
    output_words = set(output_lower.split())
    if expected_words:
        overlap = len(expected_words & output_words) / len(expected_words)
        score = 0.3 + (0.7 * overlap)

    return min(1.0, max(0.0, score))


def _parse_score(value) -> float:
    """Parse a score value, handling various LLM output formats."""
    if isinstance(value, (int, float)):
        return min(1.0, max(0.0, float(value)))
    try:
        return min(1.0, max(0.0, float(str(value).strip())))
    except (ValueError, TypeError):
        return 0.5  # Default to neutral on parse failure


def tool_selection_metric(example: dspy.Example, prediction: dspy.Prediction, trace=None) -> float:
    """DSPy-compatible metric for tool selection optimization.

    Evaluates the correctness of the predicted tool name and its arguments.
    """
    # Expected tool and args
    expected_tool = getattr(example, "expected_tool", "") or ""
    expected_args = getattr(example, "expected_args", {}) or {}

    # Predicted tool and args
    predicted_tool = getattr(prediction, "predicted_tool", "") or ""
    predicted_args_raw = getattr(prediction, "predicted_args", "") or ""

    if not predicted_tool:
        return 0.0

    # 1. Score tool name match (0.6 weight)
    expected_clean = expected_tool.strip().lower()
    predicted_clean = predicted_tool.strip().strip("'\"").strip().lower()

    tool_match_score = 0.0
    if expected_clean == predicted_clean:
        tool_match_score = 1.0

    # 2. Score arguments match (0.4 weight)
    import json
    parsed_args = {}
    if isinstance(predicted_args_raw, dict):
        parsed_args = predicted_args_raw
    elif isinstance(predicted_args_raw, str) and predicted_args_raw.strip():
        # Clean JSON markdown blocks if any
        json_clean = predicted_args_raw.strip()
        if json_clean.startswith("```"):
            lines = json_clean.split("\n")
            if len(lines) > 2:
                json_clean = "\n".join(lines[1:-1]).strip()
        try:
            parsed_args = json.loads(json_clean)
        except Exception:
            pass

    args_match_score = 0.0
    if expected_args:
        total_keys = len(expected_args)
        matching_keys = 0
        for k, expected_val in expected_args.items():
            if k in parsed_args:
                pred_val = parsed_args[k]
                if str(expected_val).strip().lower() == str(pred_val).strip().lower():
                    matching_keys += 1
        args_match_score = matching_keys / total_keys if total_keys > 0 else 1.0
    else:
        if not parsed_args:
            args_match_score = 1.0

    score = (tool_match_score * 0.6) + (args_match_score * 0.4)
    return min(1.0, max(0.0, score))
