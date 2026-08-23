# tests/test_mutation_daemon.py
from sakthai.governance.mutation_daemon import (
    MutationDaemon,
    MutationOperator,
    mutate_source_code,
)


def test_mutate_source_code_invert_comparison():
    code = "if a < b:\n    return True\n"
    mutated = mutate_source_code(code, MutationOperator.INVERT_COMPARISON)
    assert (
        "if a >= b:" in mutated
        or "if a > b:" in mutated
        or "if a <= b:" in mutated
        or "<=" in mutated
    )


def test_mutation_daemon_evaluate():
    daemon = MutationDaemon()
    daemon.register_test_runner(lambda code: "FAIL" if "==" in code else "PASS")

    score = daemon.evaluate_mutation(
        source_code="if x != 0:\n    return x\n",
        operator=MutationOperator.INVERT_EQUALITY,
    )
    assert score.mutated is True
    assert score.killed is True
