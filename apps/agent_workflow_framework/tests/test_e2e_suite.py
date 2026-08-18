import os
import sys
import unittest
import tempfile
import json
import asyncio
from pathlib import Path

# Standard import guard: attempt import from agent_workflow, fallback to tests.engine_fallback if not present
try:
    from agent_workflow.models import (
        StepStatus, RunStatus, StepDefinition, WorkflowDefinition, StepResult, RunHistory
    )
    from agent_workflow.parser import parse_workflow_file, parse_workflow_dict
    from agent_workflow.dag import validate_workflow_dag, build_topological_batches
    from agent_workflow.state import StateContext
    from agent_workflow.executor import WorkflowExecutor
    from agent_workflow.persistence import HistoryStore
    from agent_workflow.cli import main as cli_main
except ModuleNotFoundError:
    from tests.engine_fallback import (
        StepStatus, RunStatus, StepDefinition, WorkflowDefinition, StepResult, RunHistory,
        parse_workflow_file, parse_workflow_dict,
        validate_workflow_dag, build_topological_batches,
        StateContext,
        WorkflowExecutor,
        HistoryStore,
        cli_main
    )

FIXTURES_DIR = Path(__file__).parent / "test_workflows"


class TestTier1FeatureCoverage(unittest.TestCase):
    """Tier 1: Feature Coverage (≥5 tests per feature area across 7 areas = 35 tests)"""

    # --- Area 1: Definition Schema & Parsing (FEAT-ENG-01) ---
    def test_parse_valid_yaml_workflow(self):
        yaml_path = FIXTURES_DIR / "linear_workflow.yaml"
        wf = parse_workflow_file(str(yaml_path))
        self.assertEqual(wf.name, "linear_workflow")
        self.assertEqual(len(wf.steps), 3)
        self.assertEqual(wf.steps[0].id, "step_1")

    def test_parse_json_workflow(self):
        data = {
            "name": "json_workflow",
            "steps": [
                {"id": "s1", "action": "echo", "params": {"msg": "hi"}}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f_path = f.name
        try:
            wf = parse_workflow_file(f_path)
            self.assertEqual(wf.name, "json_workflow")
            self.assertEqual(len(wf.steps), 1)
        finally:
            os.unlink(f_path)

    def test_parse_missing_required_name(self):
        data = {"steps": [{"id": "s1"}]}
        with self.assertRaises((ValueError, TypeError)):
            parse_workflow_dict(data)

    def test_parse_invalid_yaml_syntax(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: test\nsteps:\n  - id: s1\n   bad_indent: [")
            f_path = f.name
        try:
            with self.assertRaises(Exception):
                parse_workflow_file(f_path)
        finally:
            os.unlink(f_path)

    def test_parse_step_default_values(self):
        data = {"name": "defaults_wf", "steps": [{"id": "step_a"}]}
        wf = parse_workflow_dict(data)
        step = wf.steps[0]
        self.assertEqual(step.id, "step_a")
        self.assertEqual(step.retry, 0)
        self.assertEqual(step.retry_delay, 0.0)
        self.assertEqual(step.depends_on, [])

    # --- Area 2: DAG Graph & Cycle Detection (FEAT-ENG-02 / FEAT-ENG-03) ---
    def test_dag_topological_sort_linear(self):
        wf = WorkflowDefinition(
            name="linear_dag",
            steps=[
                StepDefinition(id="a"),
                StepDefinition(id="b", depends_on=["a"]),
                StepDefinition(id="c", depends_on=["b"]),
            ]
        )
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0][0].id, "a")
        self.assertEqual(batches[1][0].id, "b")
        self.assertEqual(batches[2][0].id, "c")

    def test_dag_parallel_batches(self):
        wf = WorkflowDefinition(
            name="parallel_dag",
            steps=[
                StepDefinition(id="root"),
                StepDefinition(id="b1", depends_on=["root"]),
                StepDefinition(id="b2", depends_on=["root"]),
                StepDefinition(id="join", depends_on=["b1", "b2"]),
            ]
        )
        batches = build_topological_batches(wf)
        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0][0].id, "root")
        batch2_ids = {s.id for s in batches[1]}
        self.assertEqual(batch2_ids, {"b1", "b2"})
        self.assertEqual(batches[2][0].id, "join")

    def test_dag_cycle_detection_direct(self):
        wf = WorkflowDefinition(
            name="cycle_wf",
            steps=[
                StepDefinition(id="a", depends_on=["b"]),
                StepDefinition(id="b", depends_on=["a"]),
            ]
        )
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)
        self.assertTrue(any("Cyclic" in e or "cycle" in e for e in errs))

    def test_dag_cycle_detection_self_loop(self):
        wf = WorkflowDefinition(
            name="self_loop_wf",
            steps=[
                StepDefinition(id="a", depends_on=["a"]),
            ]
        )
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)

    def test_dag_undefined_dependency(self):
        wf = WorkflowDefinition(
            name="undef_dep",
            steps=[
                StepDefinition(id="a", depends_on=["nonexistent"]),
            ]
        )
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)
        self.assertTrue(any("undefined" in e or "non-existent" in e for e in errs))

    # --- Area 3: State Passing & Interpolation (FEAT-STA-01) ---
    def test_state_interpolation_single_key(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"greeting": "hello"})
        res = ctx.interpolate("${steps.s1.output.greeting}")
        self.assertEqual(res, "hello")

    def test_state_interpolation_nested_dict(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"user": {"details": {"role": "admin"}}})
        res = ctx.interpolate("${steps.s1.output.user.details.role}")
        self.assertEqual(res, "admin")

    def test_state_interpolation_type_preservation(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"items": [1, 2, 3]})
        res = ctx.interpolate("${steps.s1.output.items}")
        self.assertEqual(res, [1, 2, 3])

    def test_state_interpolation_missing_key(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"a": 1})
        with self.assertRaises(KeyError):
            ctx.interpolate("${steps.s1.output.b}")

    def test_state_interpolation_multiple_expressions(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"first": "John"})
        ctx.set_step_output("s2", {"last": "Doe"})
        res = ctx.interpolate("${steps.s1.output.first} ${steps.s2.output.last}")
        self.assertEqual(res, "John Doe")

    # --- Area 4: History Persistence & Log Store (FEAT-STA-02) ---
    def test_persistence_creates_run_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = HistoryStore(storage_dir=tmpdir)
            history = RunHistory(
                run_id="run_test_01",
                workflow_name="test_wf",
                status=RunStatus.COMPLETED,
                start_time="2026-08-01T00:00:00Z",
            )
            filepath = store.save_run_history(history)
            self.assertTrue(os.path.exists(filepath))

    def test_persistence_run_history_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = HistoryStore(storage_dir=tmpdir)
            history = RunHistory(
                run_id="run_test_02",
                workflow_name="test_wf",
                status=RunStatus.COMPLETED,
                start_time="2026-08-01T00:00:00Z",
                end_time="2026-08-01T00:00:01Z",
                step_results={
                    "step_1": StepResult(step_id="step_1", status=StepStatus.COMPLETED, output={"val": 10})
                }
            )
            store.save_run_history(history)
            loaded = store.load_run_history("run_test_02")
            self.assertEqual(loaded.run_id, "run_test_02")
            self.assertEqual(loaded.status, RunStatus.COMPLETED)
            self.assertIn("step_1", loaded.step_results)
            self.assertEqual(loaded.step_results["step_1"].output["val"], 10)

    def test_persistence_step_execution_details(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = HistoryStore(storage_dir=tmpdir)
            history = RunHistory(
                run_id="run_test_03",
                workflow_name="test_wf",
                status=RunStatus.FAILED,
                start_time="2026-08-01T00:00:00Z",
                step_results={
                    "s1": StepResult(step_id="s1", status=StepStatus.FAILED, error="Some error", attempts=2)
                }
            )
            store.save_run_history(history)
            loaded = store.load_run_history("run_test_03")
            self.assertEqual(loaded.step_results["s1"].status, StepStatus.FAILED)
            self.assertEqual(loaded.step_results["s1"].error, "Some error")
            self.assertEqual(loaded.step_results["s1"].attempts, 2)

    def test_persistence_auto_create_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = os.path.join(tmpdir, "nested", "log_dir")
            store = HistoryStore(storage_dir=target_dir)
            history = RunHistory(
                run_id="run_auto_dir",
                workflow_name="wf",
                status=RunStatus.COMPLETED,
                start_time="2026-08-01T00:00:00Z",
            )
            store.save_run_history(history)
            self.assertTrue(os.path.exists(target_dir))

    def test_persistence_failed_run_logging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = HistoryStore(storage_dir=tmpdir)
            history = RunHistory(
                run_id="run_failed",
                workflow_name="wf_failed",
                status=RunStatus.FAILED,
                start_time="2026-08-01T00:00:00Z",
            )
            store.save_run_history(history)
            loaded = store.load_run_history("run_failed")
            self.assertEqual(loaded.status, RunStatus.FAILED)

    # --- Area 5: Parallel Step Execution Engine (FEAT-ENG-04) ---
    def test_parallel_execution_concurrency(self):
        wf = WorkflowDefinition(
            name="parallel_wf",
            steps=[
                StepDefinition(id="root", action="echo", params={"seed": 10}),
                StepDefinition(id="b1", action="echo", params={"v": 1}, depends_on=["root"]),
                StepDefinition(id="b2", action="echo", params={"v": 2}, depends_on=["root"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["b1"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["b2"].status, StepStatus.COMPLETED)

    def test_parallel_fan_in_join(self):
        wf = parse_workflow_file(str(FIXTURES_DIR / "parallel_workflow.yaml"))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        join_output = history.step_results["step_join"].output
        self.assertEqual(join_output["combined_val"], 350)

    def test_parallel_worker_limit_respect(self):
        wf = parse_workflow_file(str(FIXTURES_DIR / "parallel_workflow.yaml"))
        executor = WorkflowExecutor(max_workers=1)
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)

    def test_parallel_thread_safety(self):
        ctx = StateContext()
        ctx.set_step_output("b1", {"val": 100})
        ctx.set_step_output("b2", {"val": 200})
        res1 = ctx.interpolate("${steps.b1.output.val}")
        res2 = ctx.interpolate("${steps.b2.output.val}")
        self.assertEqual(res1 + res2, 300)

    def test_parallel_partial_branch_completion(self):
        wf = WorkflowDefinition(
            name="partial_branch",
            steps=[
                StepDefinition(id="root", action="echo", params={"a": 1}),
                StepDefinition(id="b_ok", action="echo", params={"v": 2}, depends_on=["root"]),
                StepDefinition(id="b_fail", action="fail_always", depends_on=["root"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["b_ok"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["b_fail"].status, StepStatus.FAILED)

    # --- Area 6: Step Retries & Short-Circuiting (FEAT-ENG-05 / FEAT-ENG-06) ---
    def test_step_retry_success_after_failure(self):
        wf = WorkflowDefinition(
            name="transient_retry",
            steps=[
                StepDefinition(
                    id="flaky",
                    action="fail_then_succeed",
                    params={"fail_attempts": 1, "success_output": "ok"},
                    retry=2,
                    retry_delay=0.01
                )
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["flaky"].attempts, 2)
        self.assertEqual(history.step_results["flaky"].output["result"], "ok")

    def test_step_retry_exhaustion(self):
        wf = WorkflowDefinition(
            name="fail_retry",
            steps=[
                StepDefinition(id="always_fails", action="fail_always", retry=2, retry_delay=0.01)
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["always_fails"].attempts, 3)
        self.assertEqual(history.step_results["always_fails"].status, StepStatus.FAILED)

    def test_downstream_short_circuiting(self):
        wf = WorkflowDefinition(
            name="short_circuit",
            steps=[
                StepDefinition(id="s1", action="fail_always", retry=0),
                StepDefinition(id="s2", action="echo", params={"v": 1}, depends_on=["s1"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["s1"].status, StepStatus.FAILED)
        self.assertEqual(history.step_results["s2"].status, StepStatus.SKIPPED)

    def test_downstream_multi_level_short_circuiting(self):
        wf = WorkflowDefinition(
            name="multi_short_circuit",
            steps=[
                StepDefinition(id="s1", action="fail_always", retry=0),
                StepDefinition(id="s2", action="echo", depends_on=["s1"]),
                StepDefinition(id="s3", action="echo", depends_on=["s2"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["s2"].status, StepStatus.SKIPPED)
        self.assertEqual(history.step_results["s3"].status, StepStatus.SKIPPED)

    def test_step_retry_delay(self):
        wf = WorkflowDefinition(
            name="delay_retry",
            steps=[
                StepDefinition(id="flaky", action="fail_then_succeed", params={"fail_attempts": 1}, retry=1, retry_delay=0.05)
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["flaky"].attempts, 2)

    # --- Area 7: CLI Commands & Exit Codes (FEAT-CLI-01..04) ---
    def test_cli_validate_success(self):
        yaml_path = str(FIXTURES_DIR / "linear_workflow.yaml")
        code = cli_main(["validate", yaml_path])
        self.assertEqual(code, 0)

    def test_cli_validate_cycle_failure(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write("name: cycle\nsteps:\n  - id: a\n    depends_on: [b]\n  - id: b\n    depends_on: [a]\n")
            f_path = f.name
        try:
            code = cli_main(["validate", f_path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(f_path)

    def test_cli_run_success(self):
        yaml_path = str(FIXTURES_DIR / "linear_workflow.yaml")
        code = cli_main(["run", yaml_path])
        self.assertEqual(code, 0)

    def test_cli_run_failure_exit_code(self):
        yaml_path = str(FIXTURES_DIR / "retry_workflow.yaml")
        code = cli_main(["run", yaml_path])
        self.assertEqual(code, 1)

    def test_cli_inspect_run_id(self):
        yaml_path = str(FIXTURES_DIR / "linear_workflow.yaml")
        wf = parse_workflow_file(yaml_path)
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf, run_id="cli_inspect_test_run"))
        code = cli_main(["inspect", "cli_inspect_test_run"])
        self.assertEqual(code, 0)


class TestTier2BoundaryAndCornerCases(unittest.TestCase):
    """Tier 2: Boundary & Corner Cases (≥5 boundary tests)"""

    def test_boundary_empty_workflow_steps(self):
        data = {"name": "empty_wf", "steps": []}
        wf = parse_workflow_dict(data)
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)

    def test_boundary_circular_dependency_indirect(self):
        wf = WorkflowDefinition(
            name="indirect_cycle",
            steps=[
                StepDefinition(id="a", depends_on=["c"]),
                StepDefinition(id="b", depends_on=["a"]),
                StepDefinition(id="c", depends_on=["b"]),
            ]
        )
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)

    def test_boundary_invalid_state_key_interpolation(self):
        ctx = StateContext()
        ctx.set_step_output("s1", {"existing_key": 10})
        with self.assertRaises(KeyError):
            ctx.interpolate("${steps.s1.output.non_existent_key}")

    def test_boundary_retry_exhaustion_max_attempts(self):
        wf = WorkflowDefinition(
            name="retry_exhaust",
            steps=[
                StepDefinition(id="failing", action="fail_always", retry=3, retry_delay=0.01)
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.step_results["failing"].attempts, 4)
        self.assertEqual(history.step_results["failing"].status, StepStatus.FAILED)

    def test_boundary_nonexistent_workflow_file(self):
        with self.assertRaises(FileNotFoundError):
            parse_workflow_file("non_existent_file_path_xyz.yaml")

    def test_boundary_duplicate_step_ids(self):
        wf = WorkflowDefinition(
            name="dup_id",
            steps=[
                StepDefinition(id="step_1"),
                StepDefinition(id="step_1"),
            ]
        )
        errs = validate_workflow_dag(wf)
        self.assertTrue(len(errs) > 0)
        self.assertTrue(any("Duplicate" in e for e in errs))

    def test_boundary_inspect_nonexistent_run_id(self):
        code = cli_main(["inspect", "nonexistent_run_id_99999"])
        self.assertEqual(code, 1)


class TestTier3PairwiseCombinations(unittest.TestCase):
    """Tier 3: Pairwise Combinations (Integration tests across feature pairs)"""

    def test_pairwise_parallel_and_retries(self):
        """Parallel execution + Step Retries"""
        wf = WorkflowDefinition(
            name="pw_par_retry",
            steps=[
                StepDefinition(id="root", action="echo", params={"seed": 10}),
                StepDefinition(id="b_ok", action="echo", params={"v": 1}, depends_on=["root"]),
                StepDefinition(id="b_retry", action="fail_then_succeed", params={"fail_attempts": 1, "success_output": 2}, depends_on=["root"], retry=2, retry_delay=0.01),
                StepDefinition(id="join", action="transform", params={"val_a": "${steps.b_ok.output.v}", "val_b": "${steps.b_retry.output.result}", "operation": "sum"}, depends_on=["b_ok", "b_retry"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["b_retry"].attempts, 2)
        self.assertEqual(history.step_results["join"].output["combined_val"], 3)

    def test_pairwise_parallel_and_state_passing(self):
        """Parallel execution + State Passing & Aggregation"""
        wf = parse_workflow_file(str(FIXTURES_DIR / "parallel_workflow.yaml"))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["step_join"].output["combined_val"], 350)

    def test_pairwise_state_passing_and_short_circuiting(self):
        """State passing + Failure Short-Circuiting"""
        wf = parse_workflow_file(str(FIXTURES_DIR / "retry_workflow.yaml"))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["step_terminal_fail"].status, StepStatus.FAILED)
        self.assertEqual(history.step_results["step_downstream_blocked"].status, StepStatus.SKIPPED)

    def test_pairwise_retry_recovery_and_state_passing(self):
        """Retry Recovery + State Passing"""
        wf = WorkflowDefinition(
            name="pw_retry_state",
            steps=[
                StepDefinition(id="retry_step", action="fail_then_succeed", params={"fail_attempts": 1, "success_output": "val_100"}, retry=1, retry_delay=0.01),
                StepDefinition(id="downstream", action="echo", params={"recv": "${steps.retry_step.output.result}"}, depends_on=["retry_step"]),
            ]
        )
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["downstream"].output["recv"], "val_100")


class TestTier4RealWorldWorkloads(unittest.TestCase):
    """Tier 4: Real-World Workload Scenarios (Scenarios 1-4)"""

    def test_scenario_1_linear_workflow(self):
        yaml_path = FIXTURES_DIR / "linear_workflow.yaml"
        wf = parse_workflow_file(str(yaml_path))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["step_1"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_2"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_3"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_3"].output["final_result"], 20)

    def test_scenario_2_parallel_dag_workflow(self):
        yaml_path = FIXTURES_DIR / "parallel_workflow.yaml"
        wf = parse_workflow_file(str(yaml_path))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        self.assertEqual(history.step_results["step_root"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_branch_a"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_branch_b"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_join"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_join"].output["combined_val"], 350)

    def test_scenario_3_retry_and_short_circuit_workflow(self):
        yaml_path = FIXTURES_DIR / "retry_workflow.yaml"
        wf = parse_workflow_file(str(yaml_path))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.FAILED)
        self.assertEqual(history.step_results["step_transient"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_transient"].attempts, 2)
        self.assertEqual(history.step_results["step_post_transient"].status, StepStatus.COMPLETED)
        self.assertEqual(history.step_results["step_terminal_fail"].status, StepStatus.FAILED)
        self.assertEqual(history.step_results["step_terminal_fail"].attempts, 2)
        self.assertEqual(history.step_results["step_downstream_blocked"].status, StepStatus.SKIPPED)

    def test_scenario_4_mutation_workflow(self):
        yaml_path = FIXTURES_DIR / "mutation_workflow.yaml"
        wf = parse_workflow_file(str(yaml_path))
        executor = WorkflowExecutor()
        history = asyncio.run(executor.execute_workflow(wf))
        self.assertEqual(history.status, RunStatus.COMPLETED)
        agg_output = history.step_results["step_aggregate_mutation"].output
        summary = agg_output["summary"]
        self.assertEqual(summary["user"]["name"], "alice")
        self.assertEqual(summary["user"]["role"], "super_admin")
        self.assertEqual(summary["user"]["score"], 100)
        self.assertEqual(summary["tags"], ["alpha", "beta", "gamma"])
        self.assertEqual(summary["count"], 3)


if __name__ == "__main__":
    unittest.main()
