"""Execution state context and template interpolation engine for agent_workflow.

Provides StateContext for storing step outputs thread-safely and interpolating
expressions of the form '${steps.STEP_ID.output.KEY}' with type preservation,
nested path resolution, and recursive data structure interpolation.
"""

import copy
import json
import re
import threading
from typing import Dict, Any, List, Optional, Union, Tuple

try:
    from agent_workflow.models import StepResult
except ImportError:
    StepResult = Any  # Type fallback if imported before models is available


class StateInterpolationError(KeyError):
    """Exception raised when template state interpolation fails.

    Inherits from KeyError for backward compatibility with dictionary lookup errors,
    while providing clear descriptive error messages for missing steps, missing output keys,
    or malformed template expressions.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class StateContext:
    """Thread-safe execution context storing step outputs and resolving template expressions.

    Supported expression format:
        ${steps.STEP_ID.output}
        ${steps.STEP_ID.output.KEY}
        ${steps.STEP_ID.output.NESTED.PATH}
    """

    # Regex for full-value expression match (type preserving):
    # e.g., "${steps.step1.output.count}" or "${ steps.step_1.output.user }"
    _EXACT_EXPR_RE = re.compile(
        r"^\s*\$\{\s*steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\s*\}\s*$"
    )

    # Regex for embedded string expression matches:
    # e.g., "Hello ${steps.s1.output.name}"
    _EMBEDDED_EXPR_RE = re.compile(
        r"\$\{\s*steps\.([a-zA-Z0-9_-]+)\.output(?:\.([a-zA-Z0-9_.-]+))?\s*\}"
    )

    # Regex detecting malformed ${steps...} constructs:
    _MALFORMED_STEPS_EXPR_RE = re.compile(
        r"\$\{\s*steps(?:\.[^\}\s]*)?\s*\}"
    )

    def __init__(self, initial_outputs: Optional[Dict[str, Dict[str, Any]]] = None):
        """Initialize StateContext with optional initial step outputs."""
        self._lock = threading.RLock()
        self._outputs: Dict[str, Dict[str, Any]] = {}
        if initial_outputs:
            for step_id, output in initial_outputs.items():
                self.set_step_output(step_id, output)

    def set_step_output(self, step_id: str, output: Dict[str, Any]) -> None:
        """Store or update output dictionary for a step thread-safely."""
        if not isinstance(step_id, str) or not step_id.strip():
            raise ValueError("Step ID must be a non-empty string.")
        if not isinstance(output, dict):
            raise ValueError(f"Output for step '{step_id}' must be a dictionary.")

        with self._lock:
            # Store a deep copy to prevent thread race conditions or external mutations
            self._outputs[step_id] = copy.deepcopy(output)

    def set_step_result(self, result: StepResult) -> None:
        """Record step output from a StepResult instance."""
        if not hasattr(result, "step_id") or not hasattr(result, "output"):
            raise TypeError("Expected an object with 'step_id' and 'output' attributes.")
        self.set_step_output(result.step_id, result.output)

    def get_step_output(self, step_id: str) -> Dict[str, Any]:
        """Retrieve output dictionary for a step thread-safely. Returns a copy."""
        with self._lock:
            if step_id not in self._outputs:
                return {}
            return copy.deepcopy(self._outputs[step_id])

    def has_step_output(self, step_id: str) -> bool:
        """Check whether output for step_id exists in state context."""
        with self._lock:
            return step_id in self._outputs

    def clear(self) -> None:
        """Clear all stored step outputs thread-safely."""
        with self._lock:
            self._outputs.clear()

    def _resolve_path(self, step_id: str, key_path: Optional[str]) -> Any:
        """Resolve step_id and optional key_path against internal outputs thread-safely."""
        with self._lock:
            if step_id not in self._outputs:
                raise StateInterpolationError(
                    f"Step '{step_id}' output not found in state context."
                )
            val = self._outputs[step_id]

        if key_path is None or key_path == "":
            return copy.deepcopy(val)

        # Check if key_path matches a direct key in dictionary first
        if isinstance(val, dict) and key_path in val:
            return copy.deepcopy(val[key_path])

        keys = key_path.split(".")
        current = val
        for idx, key in enumerate(keys):
            if isinstance(current, dict):
                if key in current:
                    current = current[key]
                else:
                    partial_path = ".".join(keys[:idx + 1])
                    raise StateInterpolationError(
                        f"Key '{key}' (path '{partial_path}') not found in step '{step_id}' output."
                    )
            elif isinstance(current, (list, tuple)):
                if key.isdigit():
                    index = int(key)
                    if 0 <= index < len(current):
                        current = current[index]
                    else:
                        list_path = ".".join(keys[:idx])
                        raise StateInterpolationError(
                            f"Index {index} out of range for list at path '{list_path}' in step '{step_id}' output."
                        )
                else:
                    raise StateInterpolationError(
                        f"Cannot access non-integer key '{key}' on list in step '{step_id}' output."
                    )
            else:
                partial_path = ".".join(keys[:idx])
                raise StateInterpolationError(
                    f"Cannot access key '{key}' on non-container object of type '{type(current).__name__}' at path '{partial_path}' in step '{step_id}' output."
                )

        return copy.deepcopy(current)

    def interpolate(self, template: Any, _depth: int = 0) -> Any:
        """Recursively interpolate state template expressions in strings, dicts, or lists."""
        if _depth > 10:
            raise ValueError("Circular or nested state interpolation depth exceeded (max 10)")
        if isinstance(template, str):
            res = self._interpolate_string(template)
            # If string resolution produced a string that contains another ${steps...} template, recursively resolve
            if isinstance(res, str) and "${steps." in res and res != template:
                return self.interpolate(res, _depth + 1)
            return res
        elif isinstance(template, dict):
            return {
                self.interpolate(k, _depth + 1) if isinstance(k, str) else k: self.interpolate(v, _depth + 1)
                for k, v in template.items()
            }
        elif isinstance(template, list):
            return [self.interpolate(item, _depth + 1) for item in template]
        elif isinstance(template, tuple):
            return tuple(self.interpolate(item, _depth + 1) for item in template)
        else:
            return template

    def _interpolate_string(self, text: str) -> Any:
        """Interpolate template string, preserving native types for exact matches."""
        # 1. Full-value exact match preserving native type
        exact_match = self._EXACT_EXPR_RE.fullmatch(text)
        if exact_match:
            step_id, key_path = exact_match.groups()
            return self._resolve_path(step_id, key_path)

        # 2. Check for malformed ${steps...} expressions
        # Find all ${steps...} tokens and check if any fail to match valid syntax
        for match in self._MALFORMED_STEPS_EXPR_RE.finditer(text):
            expr_str = match.group(0)
            if not self._EMBEDDED_EXPR_RE.fullmatch(expr_str):
                raise StateInterpolationError(
                    f"Malformed state interpolation expression '{expr_str}' in template: '{text}'"
                )

        # 3. Handle embedded string interpolation
        def replace_token(m: re.Match) -> str:
            step_id, key_path = m.groups()
            val = self._resolve_path(step_id, key_path)
            if isinstance(val, (dict, list, tuple)):
                return json.dumps(val)
            return str(val)

        return self._EMBEDDED_EXPR_RE.sub(replace_token, text)
