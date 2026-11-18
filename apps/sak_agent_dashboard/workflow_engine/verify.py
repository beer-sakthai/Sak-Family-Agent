#!/usr/bin/env python3
"""
verify.py - Master Automated Verification Runner for Agent Workflow Framework

Programmatically and via CLI executes scenario workflows (Linear, Parallel DAG, Failure & Retry, State Mutation),
validates CLI commands and exit codes (0 for success, 1 for runtime failure, 2 for validation failure),
and runs python -m unittest discover -s tests.

Exits code 0 when all tests pass, exit code 1 if any fail.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
FIXTURES_DIR = BASE_DIR / "tests" / "test_workflows"

# Resolve imports consistently when this script is launched from another
# working directory, and report missing runtime dependencies with a repair
# command instead of falling through to the fallback module's same import.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from agent_workflow.cli import main as cli_main
    from agent_workflow.executor import WorkflowExecutor
    from agent_workflow.models import RunStatus, StepStatus
    from agent_workflow.parser import parse_workflow_file
except ModuleNotFoundError as exc:
    if exc.name == "yaml":
        raise SystemExit(
            "Missing dependency 'PyYAML'. Install it with: "
            f"python -m pip install -r {BASE_DIR / 'requirements.txt'}"
        ) from exc
    raise


def print_header(title: str) -> None:
    print(
        f"\n========================================\n{title}\n========================================"
    )


def run_cli_cmd(args: list) -> int:
    """Executes CLI command via python -m subprocess if module exists, else directly calls cli_main."""
    cmd = [sys.executable, "-m", "agent_workflow.cli"] + args
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_DIR)
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
        print(
            f"[FAIL] step_transient status was {history.step_results['step_transient'].status}, expected COMPLETED."
        )
        return False
    if history.step_results["step_transient"].attempts != 2:
        print(
            f"[FAIL] step_transient attempts was {history.step_results['step_transient'].attempts}, expected 2."
        )
        return False
    if history.step_results["step_terminal_fail"].status != StepStatus.FAILED:
        print(
            f"[FAIL] step_terminal_fail status was {history.step_results['step_terminal_fail'].status}, expected FAILED."
        )
        return False
    if history.step_results["step_downstream_blocked"].status != StepStatus.SKIPPED:
        print(
            f"[FAIL] step_downstream_blocked status was {history.step_results['step_downstream_blocked'].status}, expected SKIPPED."
        )
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
    if summary.get("user", {}).get("role") != "super_admin" or summary.get("tags") != [
        "alpha",
        "beta",
        "gamma",
    ]:
        print(f"[FAIL] Scenario 4 summary output mismatch: {summary}")
        return False

    print("[PASS] Scenario 4 data mutation and aggregation verified.")
    return True


def verify_cyclic_validation() -> bool:
    print_header("CLI Validation Test: Cyclic Graph Exit Code 2")
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(
            "name: cyclic_wf\nsteps:\n  - id: step_a\n    depends_on: [step_b]\n  - id: step_b\n    depends_on: [step_a]\n"
        )
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


def verify_benchmark_baselines() -> tuple[bool, dict]:
    """Execute performance baselines for parallel fan-out and retry workloads."""
    print_header("Phase 3: Performance Baselines & Benchmark Quality")
    import asyncio
    from agent_workflow.models import StepDefinition, WorkflowDefinition

    # 1. Parallel Fan-Out Benchmark
    # 1 root step, 8 parallel worker steps, 1 join step
    steps = [
        StepDefinition(
            id="bench_root",
            action="echo",
            params={"seed": 10},
            depends_on=[],
        )
    ]
    for i in range(8):
        steps.append(
            StepDefinition(
                id=f"bench_worker_{i}",
                action="transform",
                params={"base": "${steps.bench_root.output.seed}", "multiplier": 2},
                depends_on=["bench_root"],
            )
        )
    steps.append(
        StepDefinition(
            id="bench_join",
            action="echo",
            params={"status": "done"},
            depends_on=[f"bench_worker_{i}" for i in range(8)],
        )
    )
    fanout_wf = WorkflowDefinition(
        name="bench_fanout_wf",
        description="Parallel fanout benchmark workflow",
        steps=steps,
    )

    executor = WorkflowExecutor(max_workers=4)
    start_time = time.perf_counter()
    history = asyncio.run(
        executor.execute_workflow(fanout_wf, run_id="bench_fanout_run", allow_duplicate_run_id=True)
    )
    fanout_duration = time.perf_counter() - start_time

    if history.status != RunStatus.COMPLETED:
        print(f"[FAIL] Benchmark fanout status was {history.status}, expected COMPLETED.")
        return False, {}

    total_steps = len(steps)
    throughput = total_steps / max(fanout_duration, 0.0001)
    print(
        f"[PASS] Parallel fan-out: {total_steps} steps executed in {fanout_duration * 1000:.2f}ms ({throughput:.1f} steps/s)."
    )

    # 2. Retry Recovery Benchmark
    retry_step = StepDefinition(
        id="bench_retry_step",
        action="fail_then_succeed",
        params={"fail_attempts": 1, "success_output": "benchmark_recovered"},
        retry=2,
        retry_delay=0.01,
        depends_on=[],
    )
    retry_wf = WorkflowDefinition(
        name="bench_retry_wf",
        description="Retry recovery benchmark workflow",
        steps=[retry_step],
    )

    retry_start = time.perf_counter()
    retry_history = asyncio.run(
        executor.execute_workflow(retry_wf, run_id="bench_retry_run", allow_duplicate_run_id=True)
    )
    retry_duration = time.perf_counter() - retry_start

    if retry_history.status != RunStatus.COMPLETED:
        print(f"[FAIL] Benchmark retry status was {retry_history.status}, expected COMPLETED.")
        return False, {}
    step_res = retry_history.step_results["bench_retry_step"]
    if step_res.attempts != 2:
        print(f"[FAIL] Benchmark retry step attempts was {step_res.attempts}, expected 2.")
        return False, {}
    print(f"[PASS] Retry recovery: recovered in {retry_duration * 1000:.2f}ms (2 attempts).")

    benchmark_data = {
        "parallel_fanout": {
            "step_count": total_steps,
            "max_workers": 4,
            "duration_ms": round(fanout_duration * 1000, 2),
            "throughput_steps_per_sec": round(throughput, 2),
            "status": "PASS",
        },
        "retry_recovery": {
            "attempts": 2,
            "retry_delay_s": 0.01,
            "duration_ms": round(retry_duration * 1000, 2),
            "status": "PASS",
        },
    }
    return True, benchmark_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Master Automated Verification Runner for Agent Workflow Framework"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON evaluation summary to stdout",
    )
    parser.add_argument(
        "--summary-file",
        type=str,
        default=None,
        help="Path to write machine-readable JSON evaluation summary file",
    )
    args = parser.parse_args(argv)

    import tempfile

    if not args.json:
        print("Starting E2E Master Verification Runner (verify.py)...")

    phase_results = {}
    benchmark_data = {}

    with tempfile.TemporaryDirectory() as tmp_dir:
        os.environ["AGENT_WORKFLOW_STORAGE_DIR"] = tmp_dir
        os.environ["SAKTHAI_HOME"] = tmp_dir

        unittest_pass = verify_unittest_suite()
        phase_results["unittest_suite"] = {"passed": unittest_pass}

        adv_pass = verify_adversarial_suite()
        phase_results["adversarial_suite"] = {"passed": adv_pass}

        sc1_pass = verify_scenario_1()
        phase_results["scenario_1_linear"] = {"passed": sc1_pass}

        sc2_pass = verify_scenario_2()
        phase_results["scenario_2_parallel"] = {"passed": sc2_pass}

        sc3_pass = verify_scenario_3()
        phase_results["scenario_3_retry"] = {"passed": sc3_pass}

        sc4_pass = verify_scenario_4()
        phase_results["scenario_4_mutation"] = {"passed": sc4_pass}

        cyclic_pass = verify_cyclic_validation()
        phase_results["cyclic_validation"] = {"passed": cyclic_pass}

        bench_pass, bench_metrics = verify_benchmark_baselines()
        phase_results["benchmark_baselines"] = {"passed": bench_pass}
        benchmark_data = bench_metrics

    all_passed = all(p["passed"] for p in phase_results.values())
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "all_passed": all_passed,
        "total_phases": len(phase_results),
        "passed_phases": sum(1 for p in phase_results.values() if p["passed"]),
        "failed_phases": sum(1 for p in phase_results.values() if not p["passed"]),
        "phases": phase_results,
        "benchmarks": benchmark_data,
    }

    if args.summary_file:
        summary_path = Path(args.summary_file)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2))
        if not args.json:
            print(f"\n[INFO] Machine-readable evaluation summary written to {summary_path}")

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        if all_passed:
            print("\n========================================")
            print("ALL VERIFICATION SCENARIOS AND TESTS PASSED!")
            print("========================================")
        else:
            print("\n========================================")
            print("VERIFICATION FAILED: ONE OR MORE SCENARIOS FAILED.")
            print("========================================")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
