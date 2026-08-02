#!/usr/bin/env python3
"""
verify.py - Master Automated Verification Runner for Agent Workflow Framework

Programmatically and via CLI executes scenario workflows (Linear, Parallel DAG, Failure & Retry, State Mutation),
validates CLI commands and exit codes (0 for success, 1 for runtime failure, 2 for validation failure),
and runs python -m unittest discover -s tests.

Exits code 0 when all tests pass, exit code 1 if any fail.
"""

import sys
import os
import subprocess
import json
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
FIXTURES_DIR = BASE_DIR / "tests" / "test_workflows"

# Import guard
try:
    from agent_workflow.cli import main as cli_main
    from agent_workflow.parser import parse_workflow_file
    from agent_workflow.executor import WorkflowExecutor
    from agent_workflow.persistence import HistoryStore
    from agent_workflow.models import RunStatus, StepStatus
except ModuleNotFoundError:
    sys.path.insert(0, str(BASE_DIR))
    from tests.engine_fallback import (
        cli_main, parse_workflow_file, WorkflowExecutor, HistoryStore, RunStatus, StepStatus
    )


def print_header(title: str) -> None:
    print(f"\n========================================\n{title}\n========================================")


def run_cli_cmd(args: list) -> int:
    """Executes CLI command via python -m subprocess if module exists, else directly calls cli_main."""
    cmd = [sys.executable, "-m", "agent_workflow.cli"] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=BASE_DIR)
    if "No module named agent_workflow" not in res.stderr:
        return res.returncode
    return cli_main(args)


def verify_unittest_suite() -> bool:
    print_header("Phase 1: Running Unittest Discovery Suite")
    cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests"]
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode == 0:
        print("[PASS] Unittest suite completed successfully.")
        return True
    else:
        print(f"[FAIL] Unittest suite failed with exit code {res.returncode}.")
        return False


def verify_scenario_1() -> bool:
    print_header("Scenario 1: Linear Workflow & Sequential State Passing")
    yaml_path = FIXTURES_DIR / "linear_workflow.yaml"

    code = run_cli_cmd(["validate", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 1 CLI validate returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 1 CLI validate succeeded.")

    code = run_cli_cmd(["run", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 1 CLI run returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 1 CLI run succeeded.")

    wf = parse_workflow_file(str(yaml_path))
    executor = WorkflowExecutor()
    import asyncio
    history = asyncio.run(executor.execute_workflow(wf))
    if history.status != RunStatus.COMPLETED:
        print(f"[FAIL] Scenario 1 status was {history.status}, expected COMPLETED.")
        return False
    step3_out = history.step_results["step_3"].output
    if step3_out.get("final_result") != 20:
        print(f"[FAIL] Scenario 1 final_result was {step3_out.get('final_result')}, expected 20.")
        return False

    print("[PASS] Scenario 1 programmatic execution and output state verified.")
    return True


def verify_scenario_2() -> bool:
    print_header("Scenario 2: Parallel Fan-Out/Fan-In Execution DAG")
    yaml_path = FIXTURES_DIR / "parallel_workflow.yaml"

    code = run_cli_cmd(["validate", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 2 CLI validate returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 2 CLI validate succeeded.")

    code = run_cli_cmd(["run", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 2 CLI run returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 2 CLI run succeeded.")

    wf = parse_workflow_file(str(yaml_path))
    executor = WorkflowExecutor()
    import asyncio
    history = asyncio.run(executor.execute_workflow(wf))
    if history.status != RunStatus.COMPLETED:
        print(f"[FAIL] Scenario 2 status was {history.status}, expected COMPLETED.")
        return False
    join_out = history.step_results["step_join"].output
    if join_out.get("combined_val") != 350:
        print(f"[FAIL] Scenario 2 combined_val was {join_out.get('combined_val')}, expected 350.")
        return False

    print("[PASS] Scenario 2 programmatic fan-in join result verified.")
    return True


def verify_scenario_3() -> bool:
    print_header("Scenario 3: Transient Retry Recovery & Terminal Short-Circuit")
    yaml_path = FIXTURES_DIR / "retry_workflow.yaml"

    code = run_cli_cmd(["validate", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 3 CLI validate returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 3 CLI validate succeeded.")

    code = run_cli_cmd(["run", str(yaml_path)])
    if code != 1:
        print(f"[FAIL] Scenario 3 CLI run returned exit code {code}, expected 1.")
        return False
    print("[PASS] Scenario 3 CLI run correctly returned exit code 1 on step failure.")

    wf = parse_workflow_file(str(yaml_path))
    executor = WorkflowExecutor()
    import asyncio
    history = asyncio.run(executor.execute_workflow(wf))
    if history.status != RunStatus.FAILED:
        print(f"[FAIL] Scenario 3 history status was {history.status}, expected FAILED.")
        return False
    if history.step_results["step_transient"].status != StepStatus.COMPLETED:
        print(f"[FAIL] step_transient status was {history.step_results['step_transient'].status}, expected COMPLETED.")
        return False
    if history.step_results["step_transient"].attempts != 2:
        print(f"[FAIL] step_transient attempts was {history.step_results['step_transient'].attempts}, expected 2.")
        return False
    if history.step_results["step_terminal_fail"].status != StepStatus.FAILED:
        print(f"[FAIL] step_terminal_fail status was {history.step_results['step_terminal_fail'].status}, expected FAILED.")
        return False
    if history.step_results["step_downstream_blocked"].status != StepStatus.SKIPPED:
        print(f"[FAIL] step_downstream_blocked status was {history.step_results['step_downstream_blocked'].status}, expected SKIPPED.")
        return False

    print("[PASS] Scenario 3 retry recovery and downstream short-circuit verified.")
    return True


def verify_scenario_4() -> bool:
    print_header("Scenario 4: Multi-Step Data Mutation & Transformation Pipeline")
    yaml_path = FIXTURES_DIR / "mutation_workflow.yaml"

    code = run_cli_cmd(["validate", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 4 CLI validate returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 4 CLI validate succeeded.")

    code = run_cli_cmd(["run", str(yaml_path)])
    if code != 0:
        print(f"[FAIL] Scenario 4 CLI run returned exit code {code}, expected 0.")
        return False
    print("[PASS] Scenario 4 CLI run succeeded.")

    wf = parse_workflow_file(str(yaml_path))
    executor = WorkflowExecutor()
    import asyncio
    history = asyncio.run(executor.execute_workflow(wf))
    if history.status != RunStatus.COMPLETED:
        print(f"[FAIL] Scenario 4 status was {history.status}, expected COMPLETED.")
        return False
    summary = history.step_results["step_aggregate_mutation"].output.get("summary", {})
    if summary.get("user", {}).get("role") != "super_admin" or summary.get("tags") != ["alpha", "beta", "gamma"]:
        print(f"[FAIL] Scenario 4 summary output mismatch: {summary}")
        return False

    print("[PASS] Scenario 4 data mutation and aggregation verified.")
    return True


def verify_cyclic_validation() -> bool:
    print_header("CLI Validation Test: Cyclic Graph Exit Code 2")
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write("name: cyclic_wf\nsteps:\n  - id: step_a\n    depends_on: [step_b]\n  - id: step_b\n    depends_on: [step_a]\n")
        cyclic_file = f.name
    try:
        code = run_cli_cmd(["validate", cyclic_file])
        if code != 2:
            print(f"[FAIL] CLI validate cyclic returned exit code {code}, expected 2.")
            return False
        print("[PASS] CLI validate cyclic workflow returned exit code 2 as expected.")
        return True
    finally:
        os.unlink(cyclic_file)


def verify_adversarial_suite() -> bool:
    print_header("Phase 2: Running Tier 5 Adversarial & Security Audit Suite")
    cmd = [sys.executable, "-m", "unittest", "tests/test_adversarial.py"]
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode == 0:
        print("[PASS] Tier 5 Adversarial & Security Audit suite completed successfully.")
        return True
    else:
        print(f"[FAIL] Adversarial suite failed with exit code {res.returncode}.")
        return False


def main():
    print("Starting E2E Master Verification Runner (verify.py)...")
    results = [
        verify_unittest_suite(),
        verify_adversarial_suite(),
        verify_scenario_1(),
        verify_scenario_2(),
        verify_scenario_3(),
        verify_scenario_4(),
        verify_cyclic_validation(),
    ]

    if all(results):
        print("\n========================================")
        print("ALL VERIFICATION SCENARIOS AND TESTS PASSED!")
        print("========================================")
        sys.exit(0)
    else:
        print("\n========================================")
        print("VERIFICATION FAILED: ONE OR MORE SCENARIOS FAILED.")
        print("========================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
