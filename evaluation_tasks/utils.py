from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from functools import wraps
from pathlib import Path
from typing import Any, Literal

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

_INTRO_LINE_PATTERNS = (
    re.compile(r"For me that line is:\s*\n\s*\*\*(.*?)\*\*", re.DOTALL),
    re.compile(r"Every reply I give begins with:\s*\*\*(.*?)\*\*", re.DOTALL),
)


def get_intro_line(persona_text: str | None) -> str | None:
    """Extract required introductory line from persona text.

    Supports both 'For me that line is:' and 'Every reply I give begins with:' directives.
    """
    if not isinstance(persona_text, str):
        return None
    for pattern in _INTRO_LINE_PATTERNS:
        match = pattern.search(persona_text)
        if match:
            return match.group(1).strip()
    return None


def load_persona_soul(persona: str) -> str:
    """Return the SOUL.md text for one of the six Sak Family personas."""
    soul_path = REPO_ROOT / "personas" / persona.strip().lower() / "SOUL.md"
    return soul_path.read_text(encoding="utf-8")


def process_results_soul_following(doc: dict[str, Any], results: list[str]) -> dict[str, float]:
    """process_results hook (doc, results) -> {metric_name: score}.

    Checks if prediction starts with correct intro line extracted from doc's persona.
    """
    prediction = results[0]
    intro_line = get_intro_line(doc.get("persona"))
    if not intro_line:
        return {"score": 0.0}

    return {"score": 1.0 if prediction.strip().startswith(intro_line) else 0.0}


def _parse_prediction_as_json(prediction_string: str) -> Any:
    """Helper to safely parse a string into a JSON object.

    Returns the parsed data or None if parsing fails.
    """
    try:
        return json.loads(prediction_string.strip())
    except (json.JSONDecodeError, AttributeError):
        return None


def _parse_prediction_as_yaml(prediction_string: str) -> Any:
    """Helper to safely parse a string into a YAML object.

    Returns the parsed data or None if parsing fails.
    """
    try:
        return yaml.safe_load(prediction_string.strip())
    except (yaml.YAMLError, AttributeError):
        return None


def _make_process_results(
    parse_fn: Callable[[str], Any],
    validator_fn: Callable[[Any, dict[str, Any]], float],
) -> Callable[[dict[str, Any], list[str]], dict[str, float]]:
    """Higher-order function that builds an lm-evaluation-harness process_results hook."""

    @wraps(validator_fn)
    def process_results(doc: dict[str, Any], results: list[str]) -> dict[str, float]:
        data = parse_fn(results[0])
        if data is None:
            return {"score": 0.0}

        return {"score": validator_fn(data, doc)}

    return process_results


def _check_json_validity(data: Any, doc: dict[str, Any]) -> float:
    """Validator: the prediction is a valid JSON object."""
    return 1.0


def _check_json_key(data: Any, doc: dict[str, Any]) -> float:
    """Validator: the JSON contains a specific required key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


def _check_json_key_value_pattern(data: Any, doc: dict[str, Any]) -> float:
    """Validator: a value for a specific key matches a regex pattern from the doc."""
    key_to_check = doc.get("key_to_check")
    value_pattern = doc.get("value_pattern")
    if (
        not key_to_check
        or not value_pattern
        or not isinstance(data, dict)
        or key_to_check not in data
    ):
        return 0.0

    value = data[key_to_check]
    return 1.0 if re.match(value_pattern, str(value)) else 0.0


def _check_json_numerical_range(data: Any, doc: dict[str, Any]) -> float:
    """Validator: a JSON value for a specific key is within a numerical range."""
    key_to_check = doc.get("key_to_check")
    min_value = doc.get("min_value")
    max_value = doc.get("max_value")

    if (
        key_to_check is None
        or min_value is None
        or max_value is None
        or not isinstance(data, dict)
        or key_to_check not in data
    ):
        return 0.0

    value = data[key_to_check]
    if not isinstance(value, (int, float)):
        return 0.0

    return 1.0 if min_value <= value <= max_value else 0.0


def _check_yaml_validity(data: Any, doc: dict[str, Any]) -> float:
    """Validator: the prediction is a valid YAML document."""
    return 1.0


def _check_yaml_key(data: Any, doc: dict[str, Any]) -> float:
    """Validator: the YAML contains a specific required key from the doc."""
    key_to_check = doc.get("key_to_check")
    if not key_to_check or not isinstance(data, dict):
        return 0.0
    return 1.0 if key_to_check in data else 0.0


process_results_json_validity = _make_process_results(
    _parse_prediction_as_json, _check_json_validity
)
process_results_json_key_check = _make_process_results(_parse_prediction_as_json, _check_json_key)
process_results_json_key_value_pattern_check = _make_process_results(
    _parse_prediction_as_json, _check_json_key_value_pattern
)
process_results_json_numerical_range_check = _make_process_results(
    _parse_prediction_as_json, _check_json_numerical_range
)
process_results_yaml_validity = _make_process_results(
    _parse_prediction_as_yaml, _check_yaml_validity
)
process_results_yaml_key_check = _make_process_results(_parse_prediction_as_yaml, _check_yaml_key)


@dataclass
class BaseEvalDataPoint:
    """Standardized dataset evaluation case with three-way partition support."""

    test_case_id: str
    split: Literal["dev", "validation", "holdout"]
    prompt: str
    expected_tool: str | None = None
    max_allowed_turns: int = 5
    simulated_tool_output: str | None = None
    require_a2ui: bool = False
    expected_facts: list[str] = field(default_factory=list)
    golden_answer: str = ""
    rubric: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseEvalDataPoint:
        """Parse from dictionary matching dataset-template.json schema or flat structure."""
        test_case_id = data.get("testCaseId") or data.get("test_case_id") or data.get("id", "")
        split = data.get("split", "dev")
        if split not in ("dev", "validation", "holdout"):
            split = "dev"
        inp = data.get("input", {})
        if isinstance(inp, dict):
            prompt = inp.get("prompt") or data.get("prompt", "")
            expected_tool = inp.get("expectedTool") or data.get("expected_tool")
            max_turns = inp.get("maxAllowedTurns") or data.get("max_allowed_turns", 5)
            sim_output = inp.get("simulatedToolOutput") or data.get("simulated_tool_output")
            require_a2ui = inp.get("requireA2ui") or data.get("require_a2ui", False)
        else:
            prompt = str(inp) if inp else data.get("prompt", "")
            expected_tool = data.get("expected_tool")
            max_turns = data.get("max_allowed_turns", 5)
            sim_output = data.get("simulated_tool_output")
            require_a2ui = data.get("require_a2ui", False)

        ref = data.get("reference", {})
        if isinstance(ref, dict):
            expected_facts = ref.get("expectedFacts") or data.get("expected_facts", [])
            golden = ref.get("goldenAnswer") or data.get("golden_answer") or data.get("golden", "")
        else:
            expected_facts = data.get("expected_facts", [])
            golden = str(ref) if ref else data.get("golden_answer") or data.get("golden", "")

        return cls(
            test_case_id=str(test_case_id),
            split=split,
            prompt=prompt,
            expected_tool=expected_tool,
            max_allowed_turns=int(max_turns),
            simulated_tool_output=sim_output,
            require_a2ui=bool(require_a2ui),
            expected_facts=list(expected_facts),
            golden_answer=golden,
            rubric=data.get("rubric", ""),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)


def __getattr__(name: str) -> Any:
    """Lazy re-export of tri-modal graders to avoid circular imports."""
    if name in (
        "GradeResult",
        "BenchmarkTask",
        "BenchmarkSuiteResult",
        "CodeGrader",
        "ModelGrader",
        "PairedJudgeResult",
        "PairedBlindJudge",
        "BenchmarkSuite",
        "DEFAULT_BENCHMARK_TASKS",
        "load_benchmark_tasks",
    ):
        from . import graders

        return getattr(graders, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
