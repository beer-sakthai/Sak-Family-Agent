"""Tri-modal grading architecture adapting Anthropic Cookbook patterns.

Implements CodeGrader, ModelGrader, and BenchmarkSuite following the building_evals.ipynb
specification (code-based deterministic checks, LLM-as-a-judge rubrics, and structured
benchmark runs with markdown reporting).
"""

from __future__ import annotations

import contextlib
import json
import logging
import re
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .utils import (
    _parse_prediction_as_json,
    _parse_prediction_as_yaml,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class GradeResult:
    """Evaluation result for an individual grader check."""

    score: float
    passed: bool
    grader_type: str  # "code", "model", "human"
    feedback: str = ""
    latency_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary representation."""
        return {
            "score": round(self.score, 4),
            "passed": self.passed,
            "grader_type": self.grader_type,
            "feedback": self.feedback,
            "latency_s": round(self.latency_s, 6),
        }


@dataclass
class BenchmarkTask:
    """Benchmark task definition for evaluation."""

    id: str
    prompt: str
    golden_answer: str = ""
    grader_type: str = "code"  # "code", "model", "human"
    rubric: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary representation."""
        return asdict(self)


@dataclass
class BenchmarkSuiteResult:
    """Aggregated results across a benchmark task evaluation suite."""

    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    accuracy: float
    average_duration_s: float
    task_results: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert suite result to dictionary representation."""
        return {
            "total_tasks": self.total_tasks,
            "passed_tasks": self.passed_tasks,
            "failed_tasks": self.failed_tasks,
            "accuracy": round(self.accuracy, 4),
            "average_duration_s": round(self.average_duration_s, 4),
            "task_results": self.task_results,
        }

    def format_markdown(self) -> str:
        """Render a formatted Markdown report matching the Cookbook structure."""
        acc_pct = self.accuracy * 100.0
        lines = [
            "# Benchmark Suite Results",
            "",
            f"- **Accuracy**: {acc_pct:.1f}% ({self.passed_tasks}/{self.total_tasks})",
            f"- **Total Tasks**: {self.total_tasks}",
            f"- **Passed Tasks**: {self.passed_tasks}",
            f"- **Failed Tasks**: {self.failed_tasks}",
            f"- **Average Duration**: {self.average_duration_s:.4f}s",
            "",
            "| Task ID | Grader | Passed | Score | Latency | Feedback |",
            "| :--- | :--- | :---: | :---: | :---: | :--- |",
        ]
        for tr in self.task_results:
            icon = "✅" if tr.get("passed") else "❌"
            score_str = f"{float(tr.get('score', 0.0)):.2f}"
            lat_str = f"{float(tr.get('latency_s', 0.0)):.4f}s"
            feedback_str = str(tr.get("feedback", "")).replace("\n", " ").strip()
            if len(feedback_str) > 60:
                feedback_str = feedback_str[:57] + "..."
            lines.append(
                f"| {tr.get('task_id', '')} | {tr.get('grader_type', '')} | {icon} | "
                f"{score_str} | {lat_str} | {feedback_str} |"
            )
        return "\n".join(lines)


class CodeGrader:
    """Deterministic, code-based evaluation checks."""

    @staticmethod
    def exact_match(
        output: str,
        golden: str,
        strip: bool = True,
        case_sensitive: bool = True,
    ) -> GradeResult:
        """Evaluate exact match between output and golden reference."""
        start = time.perf_counter()
        o = output.strip() if strip else output
        g = golden.strip() if strip else golden
        if not case_sensitive:
            o = o.lower()
            g = g.lower()
        passed = o == g
        score = 1.0 if passed else 0.0
        feedback = "Exact match passed" if passed else f"Expected '{golden}', got '{output}'"
        return GradeResult(
            score=score,
            passed=passed,
            grader_type="code",
            feedback=feedback,
            latency_s=time.perf_counter() - start,
        )

    @staticmethod
    def contains_match(
        output: str,
        expected_substrings: list[str],
    ) -> GradeResult:
        """Evaluate whether output contains all expected substrings."""
        start = time.perf_counter()
        if not expected_substrings:
            return GradeResult(
                score=1.0,
                passed=True,
                grader_type="code",
                feedback="No expected substrings specified",
                latency_s=time.perf_counter() - start,
            )
        missing = [s for s in expected_substrings if s not in output]
        passed = len(missing) == 0
        score = (len(expected_substrings) - len(missing)) / len(expected_substrings)
        feedback = "All expected substrings found" if passed else f"Missing substrings: {missing}"
        return GradeResult(
            score=score,
            passed=passed,
            grader_type="code",
            feedback=feedback,
            latency_s=time.perf_counter() - start,
        )

    @staticmethod
    def regex_match(output: str, pattern: str) -> GradeResult:
        """Evaluate whether output matches the provided regular expression."""
        start = time.perf_counter()
        try:
            match = re.search(pattern, output)
            passed = match is not None
            score = 1.0 if passed else 0.0
            feedback = (
                f"Regex matched pattern: {pattern}"
                if passed
                else f"Output did not match pattern: {pattern}"
            )
        except re.error as exc:
            passed = False
            score = 0.0
            feedback = f"Invalid regex pattern '{pattern}': {exc}"
        return GradeResult(
            score=score,
            passed=passed,
            grader_type="code",
            feedback=feedback,
            latency_s=time.perf_counter() - start,
        )

    @staticmethod
    def _strip_markdown_code_fences(text: str) -> str:
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            clean = "\n".join(lines).strip()
        return clean

    @classmethod
    def json_schema_valid(
        cls,
        output: str,
        required_keys: list[str] | None = None,
    ) -> GradeResult:
        """Evaluate whether output parses as valid JSON and contains required keys."""
        start = time.perf_counter()
        clean = cls._strip_markdown_code_fences(output)
        data = _parse_prediction_as_json(clean)
        if data is None:
            try:
                data = json.loads(clean)
            except Exception as exc:
                return GradeResult(
                    score=0.0,
                    passed=False,
                    grader_type="code",
                    feedback=f"JSON parse error: {exc}",
                    latency_s=time.perf_counter() - start,
                )

        if required_keys is not None:
            if not isinstance(data, dict):
                return GradeResult(
                    score=0.0,
                    passed=False,
                    grader_type="code",
                    feedback="Parsed JSON is not an object/dictionary",
                    latency_s=time.perf_counter() - start,
                )
            missing = [k for k in required_keys if k not in data]
            passed = len(missing) == 0
            score = (
                1.0
                if not required_keys
                else (len(required_keys) - len(missing)) / len(required_keys)
            )
            feedback = (
                "Valid JSON containing all required keys"
                if passed
                else f"Missing required keys: {missing}"
            )
            return GradeResult(
                score=score,
                passed=passed,
                grader_type="code",
                feedback=feedback,
                latency_s=time.perf_counter() - start,
            )

        return GradeResult(
            score=1.0,
            passed=True,
            grader_type="code",
            feedback="Valid JSON object",
            latency_s=time.perf_counter() - start,
        )

    @classmethod
    def yaml_valid(
        cls,
        output: str,
        required_keys: list[str] | None = None,
    ) -> GradeResult:
        """Evaluate whether output parses as valid YAML and contains required keys."""
        start = time.perf_counter()
        clean = cls._strip_markdown_code_fences(output)
        data = _parse_prediction_as_yaml(clean)
        if data is None:
            try:
                data = yaml.safe_load(clean)
            except Exception as exc:
                return GradeResult(
                    score=0.0,
                    passed=False,
                    grader_type="code",
                    feedback=f"YAML parse error: {exc}",
                    latency_s=time.perf_counter() - start,
                )
        if data is None and clean:
            return GradeResult(
                score=0.0,
                passed=False,
                grader_type="code",
                feedback="YAML document is empty or comment-only",
                latency_s=time.perf_counter() - start,
            )

        if required_keys is not None:
            if not isinstance(data, dict):
                return GradeResult(
                    score=0.0,
                    passed=False,
                    grader_type="code",
                    feedback="Parsed YAML is not an object/dictionary",
                    latency_s=time.perf_counter() - start,
                )
            missing = [k for k in required_keys if k not in data]
            passed = len(missing) == 0
            score = (
                1.0
                if not required_keys
                else (len(required_keys) - len(missing)) / len(required_keys)
            )
            feedback = (
                "Valid YAML containing all required keys"
                if passed
                else f"Missing required keys: {missing}"
            )
            return GradeResult(
                score=score,
                passed=passed,
                grader_type="code",
                feedback=feedback,
                latency_s=time.perf_counter() - start,
            )

        return GradeResult(
            score=1.0,
            passed=True,
            grader_type="code",
            feedback="Valid YAML document",
            latency_s=time.perf_counter() - start,
        )

    @staticmethod
    def numerical_range(
        output: str,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> GradeResult:
        """Evaluate whether numerical value extracted from output is within [min_val, max_val]."""
        start = time.perf_counter()
        val: float | None = None
        try:
            val = float(output.strip())
        except ValueError:
            match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", output)
            if match:
                with contextlib.suppress(ValueError):
                    val = float(match.group(0))

        if val is None:
            return GradeResult(
                score=0.0,
                passed=False,
                grader_type="code",
                feedback=f"Could not extract numerical value from: '{output}'",
                latency_s=time.perf_counter() - start,
            )

        if min_val is not None and val < min_val:
            return GradeResult(
                score=0.0,
                passed=False,
                grader_type="code",
                feedback=f"Value {val} is below minimum {min_val}",
                latency_s=time.perf_counter() - start,
            )
        if max_val is not None and val > max_val:
            return GradeResult(
                score=0.0,
                passed=False,
                grader_type="code",
                feedback=f"Value {val} is above maximum {max_val}",
                latency_s=time.perf_counter() - start,
            )

        return GradeResult(
            score=1.0,
            passed=True,
            grader_type="code",
            feedback=f"Value {val} is within range [{min_val}, {max_val}]",
            latency_s=time.perf_counter() - start,
        )


class ModelGrader:
    """Model-based evaluation (LLM-as-a-judge) with structured rubric."""

    @staticmethod
    def build_grader_prompt(answer: str, rubric: str, task: str = "") -> str:
        """Construct evaluation prompt following the Anthropic Cookbook standard."""
        task_section = f"<task>\n{task}\n</task>\n\n" if task else ""
        return (
            "You are an expert evaluator assessing whether an AI assistant's response "
            "correctly satisfies the task requirements and grading rubric.\n\n"
            f"{task_section}"
            f"<student_answer>\n{answer}\n</student_answer>\n\n"
            f"<rubric>\n{rubric}\n</rubric>\n\n"
            "Please grade the student's answer according to the rubric:\n"
            "1. In <thinking> tags, analyze the student's answer against each criterion in "
            "the rubric step by step.\n"
            "2. In <correctness> tags, output EXACTLY 'correct' if the answer satisfies the rubric, "
            "or 'incorrect' if it does not."
        )

    @classmethod
    def grade(
        cls,
        output: str,
        rubric: str,
        task: str = "",
        call_fn: Callable[[str], str] | None = None,
    ) -> GradeResult:
        """Grade an output against a rubric using an LLM evaluator."""
        start = time.perf_counter()
        prompt = cls.build_grader_prompt(answer=output, rubric=rubric, task=task)

        if call_fn is not None:
            raw = call_fn(prompt)
        else:
            try:
                from sakthai.agent.loop import run_agent

                result = run_agent(prompt, fast=True, stateless=True, tools=())
                raw = result.text
            except Exception as exc:
                logger.warning("Default model grader dispatch failed: %s", exc)
                return GradeResult(
                    score=0.0,
                    passed=False,
                    grader_type="model",
                    feedback=f"Model evaluation unavailable: {exc}",
                    latency_s=time.perf_counter() - start,
                )

        thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw, re.DOTALL | re.IGNORECASE)
        thinking = thinking_match.group(1).strip() if thinking_match else ""

        correctness_match = re.search(
            r"<correctness>(.*?)</correctness>", raw, re.DOTALL | re.IGNORECASE
        )
        if correctness_match:
            verdict = correctness_match.group(1).strip().lower()
            passed = "correct" in verdict and "incorrect" not in verdict
        else:
            text_lower = raw.lower()
            if (
                "correctness: correct" in text_lower
                or "<correctness>correct" in text_lower
                or ("correct" in text_lower and "incorrect" not in text_lower)
            ):
                passed = True
            else:
                passed = False

        score = 1.0 if passed else 0.0
        feedback = thinking if thinking else raw.strip()

        return GradeResult(
            score=score,
            passed=passed,
            grader_type="model",
            feedback=feedback,
            latency_s=time.perf_counter() - start,
        )


DEFAULT_BENCHMARK_TASKS: list[BenchmarkTask] = [
    BenchmarkTask(
        id="exact_capital_thailand",
        prompt="What is the capital of Thailand?",
        golden_answer="Bangkok",
        grader_type="code",
        metadata={"match_type": "exact", "strip": True, "case_sensitive": False},
    ),
    BenchmarkTask(
        id="math_arithmetic_product",
        prompt="What is 17 * 4?",
        golden_answer="68",
        grader_type="code",
        metadata={"match_type": "exact", "strip": True},
    ),
    BenchmarkTask(
        id="code_contains_greeting",
        prompt="Write a brief greeting to Beer.",
        golden_answer="Beer",
        grader_type="code",
        metadata={"match_type": "contains", "expected_substrings": ["Beer"]},
    ),
    BenchmarkTask(
        id="code_regex_run_id",
        prompt="Generate a run ID with prefix run- followed by digits.",
        golden_answer="run-12345",
        grader_type="code",
        metadata={"match_type": "regex", "pattern": r"^run-\d+$"},
    ),
    BenchmarkTask(
        id="code_json_status",
        prompt="Output a JSON object with 'status' and 'code' keys.",
        golden_answer='{"status": "ok", "code": 200}',
        grader_type="code",
        metadata={"match_type": "json", "required_keys": ["status", "code"]},
    ),
    BenchmarkTask(
        id="code_yaml_config",
        prompt="Output a YAML config with 'name' and 'version' keys.",
        golden_answer="name: sakthai\nversion: 1.0",
        grader_type="code",
        metadata={"match_type": "yaml", "required_keys": ["name", "version"]},
    ),
    BenchmarkTask(
        id="code_cpu_temp_range",
        prompt="Report an acceptable operating temperature in Celsius (between 20 and 85).",
        golden_answer="45.0",
        grader_type="code",
        metadata={"match_type": "numerical_range", "min_val": 20.0, "max_val": 85.0},
    ),
    BenchmarkTask(
        id="model_cicd_explanation",
        prompt="Explain CI/CD in one sentence.",
        golden_answer="CI/CD automates software integration, testing, and deployment to deliver changes reliably and quickly.",
        grader_type="model",
        rubric="The response must explain continuous integration or continuous deployment clearly and accurately.",
    ),
]


class BenchmarkSuite:
    """Benchmark evaluation runner coordinating code, model, and human graders."""

    def __init__(
        self,
        tasks: list[BenchmarkTask] | None = None,
        persona: str | None = None,
        generate_fn: Callable[[str], str] | None = None,
        model_grader_fn: Callable[[str], str] | None = None,
    ) -> None:
        self.tasks = list(tasks) if tasks is not None else list(DEFAULT_BENCHMARK_TASKS)
        self.persona = persona
        self.generate_fn = generate_fn
        self.model_grader_fn = model_grader_fn

    def _default_generate(self, prompt: str) -> str:
        try:
            from sakthai.agent.loop import DEFAULT_MODEL, run_agent

            kwargs: dict[str, Any] = {
                "fast": True,
                "stateless": True,
                "tools": (),
                "model": DEFAULT_MODEL,
            }
            if self.persona:
                kwargs["persona"] = self.persona
            res = run_agent(prompt, **kwargs)
            return res.text
        except Exception as exc:
            logger.warning("Default benchmark generator dispatch failed: %s", exc)
            return ""

    def run(
        self,
        tasks: list[BenchmarkTask] | None = None,
        generate_fn: Callable[[str], str] | None = None,
    ) -> BenchmarkSuiteResult:
        """Run all tasks in the suite and compute aggregated benchmark metrics."""
        tasks_to_run = self.tasks if tasks is None else list(tasks)
        gen = generate_fn or self.generate_fn

        task_results: list[dict[str, Any]] = []

        for task in tasks_to_run:
            t_start = time.perf_counter()
            if gen is not None:
                output = gen(task.prompt)
            else:
                output = self._default_generate(task.prompt)

            grade_res: GradeResult
            if task.grader_type == "model":
                call_fn = self.model_grader_fn or gen
                grade_res = ModelGrader.grade(
                    output=output,
                    rubric=task.rubric,
                    task=task.prompt,
                    call_fn=call_fn,
                )
            elif task.grader_type == "human":
                passed = output.strip() == task.golden_answer.strip()
                grade_res = GradeResult(
                    score=1.0 if passed else 0.0,
                    passed=passed,
                    grader_type="human",
                    feedback=(
                        "Exact match against human golden baseline"
                        if passed
                        else "Golden baseline mismatch"
                    ),
                    latency_s=0.0,
                )
            else:
                m_type = task.metadata.get("match_type", "exact")
                if m_type == "contains":
                    substrings = task.metadata.get("expected_substrings")
                    if not substrings and task.golden_answer:
                        substrings = [task.golden_answer]
                    grade_res = CodeGrader.contains_match(output, substrings or [])
                elif m_type == "regex":
                    pattern = task.metadata.get("pattern", task.golden_answer)
                    grade_res = CodeGrader.regex_match(output, pattern)
                elif m_type == "json":
                    keys = task.metadata.get("required_keys")
                    grade_res = CodeGrader.json_schema_valid(output, required_keys=keys)
                elif m_type == "yaml":
                    keys = task.metadata.get("required_keys")
                    grade_res = CodeGrader.yaml_valid(output, required_keys=keys)
                elif m_type == "numerical_range":
                    grade_res = CodeGrader.numerical_range(
                        output,
                        min_val=task.metadata.get("min_val"),
                        max_val=task.metadata.get("max_val"),
                    )
                else:
                    grade_res = CodeGrader.exact_match(
                        output,
                        task.golden_answer,
                        strip=task.metadata.get("strip", True),
                        case_sensitive=task.metadata.get("case_sensitive", True),
                    )

            duration_s = time.perf_counter() - t_start

            task_results.append(
                {
                    "task_id": task.id,
                    "prompt": task.prompt,
                    "output": output,
                    "golden_answer": task.golden_answer,
                    "grader_type": task.grader_type,
                    "score": grade_res.score,
                    "passed": grade_res.passed,
                    "feedback": grade_res.feedback,
                    "latency_s": grade_res.latency_s,
                    "duration_s": duration_s,
                }
            )

        total_tasks = len(tasks_to_run)
        passed_tasks = sum(1 for tr in task_results if tr["passed"])
        failed_tasks = total_tasks - passed_tasks
        accuracy = (passed_tasks / total_tasks) if total_tasks > 0 else 0.0
        avg_dur = (
            (sum(tr["duration_s"] for tr in task_results) / total_tasks) if total_tasks > 0 else 0.0
        )

        return BenchmarkSuiteResult(
            total_tasks=total_tasks,
            passed_tasks=passed_tasks,
            failed_tasks=failed_tasks,
            accuracy=accuracy,
            average_duration_s=avg_dur,
            task_results=task_results,
        )


def load_benchmark_tasks(suite: str | None = None) -> list[BenchmarkTask]:
    """Load benchmark tasks by suite name or file path."""
    if not suite or suite.strip().lower() == "default":
        return list(DEFAULT_BENCHMARK_TASKS)

    p = Path(suite)
    if not p.is_file():
        eval_dir = REPO_ROOT / "evaluation_tasks"
        candidates = [
            eval_dir / f"{suite}.jsonl",
            eval_dir / f"{suite}_dataset.jsonl",
            eval_dir / f"{suite}.yaml",
            eval_dir / f"{suite}.json",
        ]
        for c in candidates:
            if c.is_file():
                p = c
                break

    if not p.is_file():
        logger.warning("Suite '%s' not found as a file; using default benchmark tasks", suite)
        return list(DEFAULT_BENCHMARK_TASKS)

    tasks: list[BenchmarkTask] = []
    if p.suffix == ".jsonl":
        for idx, line in enumerate(p.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                task_id = row.get("id") or f"{p.stem}_{idx}"
                prompt = row.get("prompt") or row.get("input") or row.get("question") or ""
                if "persona" in row and "question" in row:
                    prompt = f"{row['persona']}\n\nQuestion: {row['question']}"
                golden = row.get("golden") or row.get("answer") or row.get("answer_json") or ""
                grader_type = row.get("grader_type", "code")
                rubric = row.get("rubric", "")
                metadata = row.get("metadata", {})
                if not metadata and "answer_json" in row:
                    metadata = {"match_type": "json"}
                tasks.append(
                    BenchmarkTask(
                        id=task_id,
                        prompt=prompt,
                        golden_answer=golden,
                        grader_type=grader_type,
                        rubric=rubric,
                        metadata=metadata,
                    )
                )
            except Exception as exc:
                logger.warning("Failed parsing task row %d in %s: %s", idx, p, exc)
    elif p.suffix in (".yaml", ".yml"):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    tasks.append(
                        BenchmarkTask(
                            id=item.get("id", f"{p.stem}_{idx}"),
                            prompt=item.get("prompt", ""),
                            golden_answer=item.get("golden_answer", ""),
                            grader_type=item.get("grader_type", "code"),
                            rubric=item.get("rubric", ""),
                            metadata=item.get("metadata", {}),
                        )
                    )
    elif p.suffix == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for idx, item in enumerate(data):
                if isinstance(item, dict):
                    tasks.append(
                        BenchmarkTask(
                            id=item.get("id", f"{p.stem}_{idx}"),
                            prompt=item.get("prompt", ""),
                            golden_answer=item.get("golden_answer", ""),
                            grader_type=item.get("grader_type", "code"),
                            rubric=item.get("rubric", ""),
                            metadata=item.get("metadata", {}),
                        )
                    )

    return tasks if tasks else list(DEFAULT_BENCHMARK_TASKS)
