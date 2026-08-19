"""Continuous Mutation Testing Governance Daemon."""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass


class MutationOperator(enum.StrEnum):
    INVERT_COMPARISON = "invert_comparison"
    INVERT_EQUALITY = "invert_equality"
    REPLACE_BOOLEAN = "replace_boolean"


@dataclass
class MutationResult:
    original_code: str
    mutated_code: str
    operator: MutationOperator
    mutated: bool
    killed: bool
    output_log: str = ""


def mutate_source_code(code: str, operator: MutationOperator) -> str:
    """Apply AST/regex level mutations to test test suite robustness."""
    if operator == MutationOperator.INVERT_COMPARISON:
        if " < " in code:
            return code.replace(" < ", " >= ", 1)
        if " > " in code:
            return code.replace(" > ", " <= ", 1)
        if " <= " in code:
            return code.replace(" <= ", " > ", 1)
        if " >= " in code:
            return code.replace(" >= ", " < ", 1)

    elif operator == MutationOperator.INVERT_EQUALITY:
        if " != " in code:
            return code.replace(" != ", " == ", 1)
        if " == " in code:
            return code.replace(" == ", " != ", 1)

    elif operator == MutationOperator.REPLACE_BOOLEAN:
        if "True" in code:
            return code.replace("True", "False", 1)
        if "False" in code:
            return code.replace("False", "True", 1)

    return code


class MutationDaemon:
    """Evaluates mutation survival rate across agent source files."""

    def __init__(self) -> None:
        self._test_runner: Callable[[str], str] | None = None

    def register_test_runner(self, runner_fn: Callable[[str], str]) -> None:
        self._test_runner = runner_fn

    def evaluate_mutation(
        self,
        source_code: str,
        operator: MutationOperator,
    ) -> MutationResult:
        mutated = mutate_source_code(source_code, operator)
        is_mutated = mutated != source_code

        killed = False
        output = ""
        if is_mutated and self._test_runner:
            res = self._test_runner(mutated)
            output = res
            if "FAIL" in res or "ERROR" in res:
                killed = True

        return MutationResult(
            original_code=source_code,
            mutated_code=mutated,
            operator=operator,
            mutated=is_mutated,
            killed=killed,
            output_log=output,
        )
