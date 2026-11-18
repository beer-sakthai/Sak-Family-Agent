"""GitBasedOrganism wrapper for code evolution.

Wraps a tool source file or code string as an evolvable organism.
Enforces AST syntax validation, function signature freezing, unified diff
generation, checkpoints, and rollback capabilities.
"""

from __future__ import annotations

import ast
import difflib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OrganismMutationRecord:
    """Record of an applied or rejected code mutation."""

    generation: int
    diff: str
    valid_syntax: bool
    safe: bool
    reason: str = ""


class GitBasedOrganism:
    """Wraps Python source code as an organism for Darwinian evolution.

    Guarantees:
    - AST syntax validation prior to accepting mutations.
    - Public function signature preservation (no breaking changes).
    - Unified diff calculation against the immutable baseline.
    - Checkpoint stack with complete rollback support.
    """

    def __init__(
        self,
        source_code: str | None = None,
        file_path: str | Path | None = None,
    ) -> None:
        self.file_path: Path | None = Path(file_path).resolve() if file_path else None
        if source_code is not None:
            self.baseline_content: str = source_code
        elif self.file_path and self.file_path.exists():
            self.baseline_content = self.file_path.read_text(encoding="utf-8")
        else:
            raise ValueError("Either source_code or existing file_path must be provided.")

        self.current_content: str = self.baseline_content
        self.checkpoints: list[str] = [self.baseline_content]
        self.mutation_history: list[OrganismMutationRecord] = []

        # Validate baseline syntax on creation
        if not self.validate_syntax(self.baseline_content):
            raise SyntaxError("Baseline source code has invalid Python syntax.")

        self._baseline_signatures = self.extract_function_signatures(self.baseline_content)

    @staticmethod
    def validate_syntax(code: str) -> bool:
        """Return True if code parses as valid Python AST, False otherwise."""
        try:
            ast.parse(code)
            return True
        except (SyntaxError, ValueError):
            return False

    @staticmethod
    def extract_function_signatures(code: str) -> dict[str, list[str]]:
        """Extract top-level and class function names and parameter lists."""
        signatures: dict[str, list[str]] = {}
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return signatures

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arg_names = [arg.arg for arg in node.args.args]
                signatures[node.name] = arg_names
        return signatures

    def validate_safety(self, candidate_code: str) -> tuple[bool, str]:
        """Validate syntax and frozen function signature contracts."""
        if not self.validate_syntax(candidate_code):
            return False, "Candidate code has invalid Python syntax."

        candidate_signatures = self.extract_function_signatures(candidate_code)

        # Baseline signatures must be preserved
        for fn_name, baseline_args in self._baseline_signatures.items():
            if fn_name not in candidate_signatures:
                return False, f"Signature violation: baseline function '{fn_name}' was removed."
            cand_args = candidate_signatures[fn_name]
            if cand_args != baseline_args:
                return (
                    False,
                    f"Signature violation for '{fn_name}': expected args {baseline_args}, got {cand_args}.",
                )

        return True, "Safe"

    def apply_mutation(
        self,
        mutated_code: str,
        generation: int = 0,
        force: bool = False,
    ) -> bool:
        """Validate and apply a mutation, saving checkpoint and writing to file if set."""
        safe, reason = self.validate_safety(mutated_code) if not force else (True, "Forced")

        diff = self.compute_diff(self.current_content, mutated_code)
        self.mutation_history.append(
            OrganismMutationRecord(
                generation=generation,
                diff=diff,
                valid_syntax=self.validate_syntax(mutated_code),
                safe=safe,
                reason=reason,
            )
        )

        if not safe:
            return False

        self.checkpoints.append(self.current_content)
        self.current_content = mutated_code

        if self.file_path and self.file_path.exists():
            self.file_path.write_text(self.current_content, encoding="utf-8")

        return True

    def rollback(self) -> str:
        """Roll back to the previous checkpoint or baseline."""
        if len(self.checkpoints) > 1:
            self.current_content = self.checkpoints.pop()
        else:
            self.current_content = self.baseline_content

        if self.file_path and self.file_path.exists():
            self.file_path.write_text(self.current_content, encoding="utf-8")

        return self.current_content

    def reset_to_baseline(self) -> str:
        """Reset organism back to immutable original baseline."""
        self.current_content = self.baseline_content
        self.checkpoints = [self.baseline_content]
        if self.file_path and self.file_path.exists():
            self.file_path.write_text(self.current_content, encoding="utf-8")
        return self.current_content

    @staticmethod
    def compute_diff(original: str, modified: str, from_name: str = "baseline", to_name: str = "mutation") -> str:
        """Compute unified diff between two code strings."""
        orig_lines = original.splitlines(keepends=True)
        mod_lines = modified.splitlines(keepends=True)
        diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=from_name, tofile=to_name)
        return "".join(diff)

    def diff(self) -> str:
        """Unified diff of current mutated code against initial baseline."""
        return self.compute_diff(self.baseline_content, self.current_content)
