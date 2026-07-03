"""Evaluation dataset generation for hermes-agent-self-evolution.

Sources:
A) Synthetic generation — LLM reads a skill/tool/prompt and generates test cases
B) SessionDB mining — extract real usage patterns and score with LLM-as-judge
C) Golden sets — hand-curated JSONL files
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

import dspy

from evolution.core.config import EvolutionConfig


@dataclass
class EvalExample:
    """A single evaluation example."""

    task_input: str  # What the user asks
    expected_behavior: str  # Rubric — what a good response looks like
    difficulty: str = "medium"  # easy, medium, hard
    category: str = "general"  # Category for stratified eval
    source: str = "synthetic"  # synthetic, sessiondb, golden

    def to_dict(self) -> dict:
        return {
            "task_input": self.task_input,
            "expected_behavior": self.expected_behavior,
            "difficulty": self.difficulty,
            "category": self.category,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EvalExample":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class EvalDataset:
    """Train/val/holdout split of evaluation examples."""

    train: list[EvalExample] = field(default_factory=list)
    val: list[EvalExample] = field(default_factory=list)
    holdout: list[EvalExample] = field(default_factory=list)

    @property
    def all_examples(self) -> list[EvalExample]:
        return self.train + self.val + self.holdout

    def save(self, path: Path):
        """Save dataset splits to JSONL files."""
        path.mkdir(parents=True, exist_ok=True)
        for split_name, split_data in [
            ("train", self.train),
            ("val", self.val),
            ("holdout", self.holdout),
        ]:
            with open(path / f"{split_name}.jsonl", "w", encoding="utf-8") as f:
                for ex in split_data:
                    f.write(json.dumps(ex.to_dict()) + "\n")

    @classmethod
    def load(cls, path: Path) -> "EvalDataset":
        """Load dataset splits from JSONL files."""
        dataset = cls()
        for split_name in ["train", "val", "holdout"]:
            split_file = path / f"{split_name}.jsonl"
            if split_file.exists():
                examples = []
                with open(split_file) as f:
                    for line in f:
                        if line.strip():
                            examples.append(EvalExample.from_dict(json.loads(line)))
                setattr(dataset, split_name, examples)
        return dataset

    def to_dspy_examples(self, split: str = "train") -> list[dspy.Example]:
        """Convert a split to DSPy Example objects."""
        data = getattr(self, split)
        return [
            dspy.Example(
                task_input=ex.task_input,
                expected_behavior=ex.expected_behavior,
            ).with_inputs("task_input")
            for ex in data
        ]


def _shuffle_split(examples: list[EvalExample], config: EvolutionConfig) -> EvalDataset:
    """Shuffle examples and split them into train/val/holdout per the config ratios."""
    random.shuffle(examples)
    n_total = len(examples)
    n_train = max(1, int(n_total * config.train_ratio))
    n_val = max(1, int(n_total * config.val_ratio))

    return EvalDataset(
        train=examples[:n_train],
        val=examples[n_train : n_train + n_val],
        holdout=examples[n_train + n_val :],
    )


class SyntheticDatasetBuilder:
    """Generate evaluation datasets using a strong LLM.

    Reads the target artifact (skill file, tool description, etc.)
    and generates realistic (task_input, expected_behavior) pairs.
    """

    class GenerateTestCases(dspy.Signature):
        """Generate realistic evaluation test cases for an agent skill or tool.

        Given the full text of a skill/tool description, generate diverse test cases
        that would exercise different aspects of the skill. Each test case should include:
        - A realistic task_input (what a user would actually ask)
        - An expected_behavior rubric (what a good response should contain/do, NOT exact text)
        - A difficulty level (easy, medium, hard)
        - A category (what aspect of the skill this tests)
        """

        artifact_text: str = dspy.InputField(
            desc="The full text of the skill/tool/prompt being tested"
        )
        artifact_type: str = dspy.InputField(
            desc="Type: 'skill', 'tool_description', or 'prompt_section'"
        )
        num_cases: int = dspy.InputField(desc="Number of test cases to generate")
        test_cases: str = dspy.OutputField(
            desc="JSON array of test cases, each with: task_input, expected_behavior, difficulty, category"
        )

    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.generator = dspy.ChainOfThought(self.GenerateTestCases)

    @staticmethod
    def _parse_cases(text: str) -> list:
        """Parse a JSON array of test cases from raw LLM output.

        Tolerates surrounding prose and arrays truncated mid-element by the
        token cap (salvages the last complete object and closes the array).
        """
        import re

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Salvage a truncated array: keep from the first '[' to the last
        # complete object '}' and re-close the bracket.
        start = text.find("[")
        last_obj = text.rfind("}")
        if start != -1 and last_obj > start:
            try:
                return json.loads(text[start : last_obj + 1] + "]")
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse test cases from LLM output: {text[:200]}")

    def generate(
        self,
        artifact_text: str,
        artifact_type: str = "skill",
        num_cases: int | None = None,
    ) -> EvalDataset:
        """Generate a full eval dataset with train/val/holdout splits."""

        n = num_cases or self.config.eval_dataset_size

        # Configure DSPy to use the judge model for generation. Give it ample
        # output room: a 20-case JSON array easily overruns the default token
        # budget and gets truncated mid-array (unparseable).
        lm = dspy.LM(self.config.judge_model, max_tokens=8000)

        with dspy.context(lm=lm):
            result = self.generator(
                artifact_text=artifact_text,
                artifact_type=artifact_type,
                num_cases=n,
            )

        # Parse the generated test cases, tolerating extra prose around the
        # array and arrays that were truncated by the token cap.
        cases_raw = self._parse_cases(result.test_cases)

        examples = [
            EvalExample(
                task_input=c.get("task_input", ""),
                expected_behavior=c.get("expected_behavior", ""),
                difficulty=c.get("difficulty", "medium"),
                category=c.get("category", "general"),
                source="synthetic",
            )
            for c in cases_raw
            if c.get("task_input") and c.get("expected_behavior")
        ]

        return _shuffle_split(examples, self.config)


class GoldenDatasetLoader:
    """Load hand-curated evaluation datasets from JSONL files."""

    @staticmethod
    def load(path: Path) -> EvalDataset:
        """Load a golden dataset. If no splits exist, auto-split the single file."""
        if (path / "train.jsonl").exists():
            return EvalDataset.load(path)

        # Single file — auto-split
        golden_file = path if path.suffix == ".jsonl" else path / "golden.jsonl"
        if not golden_file.exists():
            raise FileNotFoundError(f"No golden dataset found at {golden_file}")

        examples = []
        with open(golden_file) as f:
            for line in f:
                if line.strip():
                    examples.append(EvalExample.from_dict(json.loads(line)))

        random.shuffle(examples)
        n = len(examples)
        n_train = max(1, int(n * 0.5))
        n_val = max(1, int(n * 0.25))

        return EvalDataset(
            train=examples[:n_train],
            val=examples[n_train : n_train + n_val],
            holdout=examples[n_train + n_val :],
        )


class LayoutDatasetBuilder:
    """
    Generates synthetic evaluation datasets specifically to test layout quality.

    The "expected_behavior" for these examples is a rubric of layout rules,
    not a specific output. This is ideal for evolving skills that produce
    structured documents, reports, or visualizations.
    """

    class GenerateLayoutTestCases(dspy.Signature):
        """
        Generate test cases that evaluate the layout and structure of an output.

        Given a skill that produces a structured artifact (like a report, a chart,
        or a formatted document), create test cases where the expected behavior is
        a checklist of layout and formatting rules.

        For example, for a chart-generating skill, the task might be "plot these results",
        and the expected_behavior rubric would be:
        - "Uses a colorblind-safe palette"
        - "Saves as PDF, not PNG"
        - "Figure size is appropriate for a single column"
        - "Axes are clearly labeled"
        - "Includes error bars"
        """

        artifact_text: str = dspy.InputField(
            desc="The full text of the skill that produces the structured output."
        )
        reference_guides: str = dspy.InputField(
            desc="Relevant reference documents that define layout best practices (e.g., visualization guides, style guides)."
        )
        num_cases: int = dspy.InputField(desc="Number of test cases to generate.")
        test_cases: str = dspy.OutputField(
            desc="JSON array of test cases. Each case must have 'task_input' and a 'expected_behavior' which is a string containing a markdown checklist of layout rules."
        )

    def __init__(self, config: EvolutionConfig):
        self.config = config
        self.generator = dspy.ChainOfThought(self.GenerateLayoutTestCases)

    def generate(
        self,
        artifact_text: str,
        reference_guides: list[str],
        num_cases: int | None = None,
    ) -> EvalDataset:
        """Generates a full eval dataset focused on layout quality."""
        n = num_cases or self.config.eval_dataset_size
        lm = dspy.LM(self.config.judge_model, max_tokens=8000)

        with dspy.context(lm=lm):
            result = self.generator(
                artifact_text=artifact_text,
                reference_guides="\n---\n".join(reference_guides),
                num_cases=n,
            )

        # Use the same robust parser from the main builder
        cases_raw = SyntheticDatasetBuilder._parse_cases(result.test_cases)

        examples = [
            EvalExample(
                task_input=c.get("task_input", ""),
                expected_behavior=c.get("expected_behavior", ""),
                difficulty=c.get("difficulty", "medium"),
                # Layout datasets are always categorized as layout, regardless
                # of what the generator model labels each case.
                category="layout",
                source="synthetic_layout",
            )
            for c in cases_raw
            if c.get("task_input") and c.get("expected_behavior")
        ]

        return _shuffle_split(examples, self.config)
